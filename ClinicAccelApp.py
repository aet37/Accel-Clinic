from Accelerometer import *
from PaintFunctions import *
from PlotFunctions import *
import os
import sys
import glob
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import matplotlib.pyplot as plt

if sys.platform == 'win32':
	import warnings
	warnings.simplefilter("ignore", UserWarning)
	sys.coinit_flags = 2
	#import pywinauto

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from datetime import datetime

# UI Setup
app = QtWidgets.QApplication(sys.argv)

class spiralDrawSystem(QtWidgets.QMainWindow):

	# UI Class initializer / LOAD THE UI
	def __init__(self):
		super(spiralDrawSystem, self).__init__()
		'''
		if sys.platform == 'win32':
			uic.loadUi('spiralDraw_win.ui', self)
		else:
			uic.loadUi('spiralDraw.ui', self)
		'''
		# Case Setup variables

		if sys.platform == 'win32':
			print('Windows Detected')
			if os.path.isdir('C:/hifu/'):
				self.basePath = 'C:/hifu/Clinic-Cases/'
				self.application_path = 'C:/hifu/Accel-Clinic/'
			else:
				self.basePath = 'C:/Users/hifuo/Clinic-Cases/'
				self.application_path = 'C:/Users/hifuo/Accel-Clinic/'

		else:
			tmpdir = os.getcwd()
			tmpdir = tmpdir.split('/')
			self.basePath = '/' + tmpdir[1] + '/'+ tmpdir[2] + '/Clinic-Cases/'
			self.application_path = '/' + tmpdir[1] + '/'+ tmpdir[2] + '/Accel-Clinic/'

		os.chdir(self.application_path)

		uic.loadUi('./spiralDraw.ui', self)
		self.move(0, 0)


		self.setWindowTitle("Clinic Tremor Assessment")

		###########################################################################################
		## Class Variables
		###########################################################################################

		# If the base directory doesnt exist, make it
		if not os.path.exists(self.basePath):
			os.mkdir(self.basePath)

		self.pt_id = ''
		self.data_save_path = ''
		self.current_trial = ''
		self.first_download = True
		self.prev_pt_lists = next(os.walk(self.basePath))[1]
		self.accel_files = []
		self.ccw_spirals = []
		self.cw_spirals = []
		self.line_spirals = []
		self.accel_trials = []
		self.accel_psds = []
		self.rh_current = 1
		self.lh_current = 1

		# Acclerometer
		self.accel_address = 'C5:02:6A:76:E4:5D'
		self.accelDevice = Accelerometer(self.accel_address)

		# Ensure device is not
		self.accelDevice.scan_connect()

		# Spiral
		self.previous_spiral_ccw = ''
		self.previous_spiral_cw = ''
		self.previous_spiral_line = ''

		# New or loaded case flag
		self.isNewCase = False

		###########################################################################################
		## Buttons / Screen Items
		###########################################################################################

		# Group Boxes
		self.trialNameSelect = self.findChild(QtWidgets.QGroupBox, 'accel_trial_sel')
		self.selectDeviceGroup = self.findChild(QtWidgets.QGroupBox, 'select_device_group')

		# Line Edits
		self.patientIdEnter = self.findChild(QtWidgets.QLineEdit, 'patientIdEnter')
		self.trialNameAccelerom = self.findChild(QtWidgets.QLineEdit, 'trialNameAccel')

		# Spin box
		self.RHValueFeild = self.findChild(QtWidgets.QSpinBox, 'clinic_rh_value')
		self.LHValueFeild = self.findChild(QtWidgets.QSpinBox, 'clinic_lh_value')

		# Push Buttons
		self.startCaseButton = self.findChild(QtWidgets.QPushButton, 'startCase')
		self.startCaseButton.clicked.connect(self.start_case)
		self.stopCaseButton = self.findChild(QtWidgets.QPushButton, 'finishCaseButton')
		self.stopCaseButton.clicked.connect(self.finish_case)
		self.loadCaseButton = self.findChild(QtWidgets.QPushButton, 'loadCaseButton')
		self.loadCaseButton.clicked.connect(self.load_case)
		self.resetBoardButton = self.findChild(QtWidgets.QPushButton, 'resetBoard')
		self.resetBoardButton.clicked.connect(self.accelDevice.scan_connect)
		self.PlotAccels = self.findChild(QtWidgets.QPushButton, 'plot_accel_aspects')
		self.PlotAccels.clicked.connect(self.plot_selected)

		self.recordAccelButton = self.findChild(QtWidgets.QPushButton, 'recordAccel')
		self.recordAccelButton.clicked.connect(self.record_accel)
		self.downloadAccelButton = self.findChild(QtWidgets.QPushButton, 'downloadAccel')
		self.downloadAccelButton.clicked.connect(self.download_accel)
		self.cancelRecordButton = self.findChild(QtWidgets.QPushButton, 'cancelRecord')
		self.cancelRecordButton.clicked.connect(self.cancel_accel_record)
		self.analyzeAccelDataButton = self.findChild(QtWidgets.QPushButton, 'analyze_accel_data')
		self.analyzeAccelDataButton.clicked.connect(self.analyze_data)
		self.generatePDF = self.findChild(QtWidgets.QPushButton, 'generate_pdf_report')
		self.generatePDF.clicked.connect(self.generate_pdf)


		# Radio Button
		self.RHRadio = self.findChild(QtWidgets.QRadioButton, 'clinic_rh_radio')
		self.LHRadio = self.findChild(QtWidgets.QRadioButton, 'clinic_lh_radio')
		self.otherRadioButton = self.findChild(QtWidgets.QRadioButton, 'otherRadio')
		self.testRadioButton = self.findChild(QtWidgets.QRadioButton, 'testRadio')
		self.penRadioButton = self.findChild(QtWidgets.QRadioButton, 'penRadio')
		self.tabletRadioButton = self.findChild(QtWidgets.QRadioButton, 'tabletRadio')
		self.spiralOnlyRadioButton = self.findChild(QtWidgets.QRadioButton, 'spiralOnlyRadio')

		# Tab Widgets
		self.aboutCaseWindow = self.findChild(QtWidgets.QWidget, 'aboutCase')
		self.accelControlWindow = self.findChild(QtWidgets.QWidget, 'accelControl')
		self.spiralControlWindow = self.findChild(QtWidgets.QWidget, 'spiralControl')
		self.spiralTab = self.findChild(QtWidgets.QWidget, 'spirals_tab')

		# Create the matplotlib canvas
		self.AccelPSDCanvas = MplCanvas(self, width=5, height=4, dpi=100)
		self.SpiralCCWCanvas = MplCanvas(self, width=5, height=4, dpi=100)
		self.SpiralCWCanvas = MplCanvas(self, width=5, height=4, dpi=100)
		self.LineCanvas = MplCanvas(self, width=5, height=4, dpi=100)

		# Graphing Widgets
		self.AccelPSDWidget = self.findChild(QtWidgets.QWidget, 'accel_psd_graph')
		self.SpiralCCWWidget = self.findChild(QtWidgets.QWidget, 'spiral_ccw_graph')
		self.SpiralCWWidget = self.findChild(QtWidgets.QWidget, 'spiral_cw_graph')
		self.LineWidget = self.findChild(QtWidgets.QWidget, 'line_graph')

		# Add the graph canvases as layouts
		layout = QtWidgets.QVBoxLayout(self.AccelPSDWidget)
		layout.addWidget(self.AccelPSDCanvas)
		self.AccelPSDWidget.setLayout(layout)

		layout = QtWidgets.QVBoxLayout(self.SpiralCCWWidget)
		layout.addWidget(self.SpiralCCWCanvas)
		self.SpiralCCWWidget.setLayout(layout)

		layout = QtWidgets.QVBoxLayout(self.SpiralCWWidget)
		layout.addWidget(self.SpiralCWCanvas)
		self.SpiralCWWidget.setLayout(layout)

		layout = QtWidgets.QVBoxLayout(self.LineWidget)
		layout.addWidget(self.LineCanvas)
		self.LineWidget.setLayout(layout)

		# Drawing Area and Buttons for Spiral Drawing Tab
		self.SpiralCCWArea = self.findChild(QtWidgets.QLabel, 'spiral_ccw_draw')
		self.SpiralCWArea = self.findChild(QtWidgets.QLabel, 'spiral_cw_draw')
		self.SpiralLineArea = self.findChild(QtWidgets.QLabel, 'line_draw')

		# Create instances of DrawingLabel
		self.drawingAreaCCW = DrawingArea('ims/spiral_ccw_big.png', self.SpiralCCWArea.parent())
		self.drawingAreaCW = DrawingArea('ims/spiral_cw_big.png', self.SpiralCWArea.parent())
		self.drawingAreaLine = DrawingArea('ims/line.png', self.SpiralLineArea.parent())

		# Set the new DrawingLabel instances to have the same geometry as the original labels
		self.drawingAreaCCW.setGeometry(self.SpiralCCWArea.geometry())
		self.drawingAreaCW.setGeometry(self.SpiralCWArea.geometry())
		self.drawingAreaLine.setGeometry(self.SpiralLineArea.geometry())

		self.drawingAreaCCW.show()
		self.drawingAreaCW.show()
		self.drawingAreaLine.show()

		self.SpiralCCWArea.hide()
		self.SpiralCWArea.hide()
		self.SpiralLineArea.hide()

		# Set background images for the drawing areas
		self.drawingAreaCCW.setImage()
		self.drawingAreaCW.setImage()
		self.drawingAreaLine.setImage()

		# Ensure the original labels are visible (if needed)
		self.SpiralCCWArea.setVisible(True)
		self.SpiralCWArea.setVisible(True)
		self.SpiralLineArea.setVisible(True)

		# Add functionality to buttons
		self.doneCCWButton = self.findChild(QtWidgets.QPushButton, 'done_ccw_button')
		self.doneCCWButton.clicked.connect(self.onDoneCCW)
		self.doneCWButton = self.findChild(QtWidgets.QPushButton, 'done_cw_button')
		self.doneCWButton.clicked.connect(self.onDoneCW)
		self.doneLineButton = self.findChild(QtWidgets.QPushButton, 'done_line_button')
		self.doneLineButton.clicked.connect(self.onDoneLine)

		self.LoadPrevCCWButton = self.findChild(QtWidgets.QPushButton, 'loadp_spiralccw_button')
		self.LoadPrevCCWButton.clicked.connect(self.onLoadPreviousCCW)
		self.LoadPrevCWButton = self.findChild(QtWidgets.QPushButton, 'loadp_spiralcw_button')
		self.LoadPrevCWButton.clicked.connect(self.onLoadPreviousCW)
		self.LoadPrevLineButton = self.findChild(QtWidgets.QPushButton, 'loadp_line_button')
		self.LoadPrevLineButton.clicked.connect(self.onLoadPreviousLine)

		self.ClearDrawingsButton = self.findChild(QtWidgets.QPushButton, 'clear_drawings')
		self.ClearDrawingsButton2 = self.findChild(QtWidgets.QPushButton, 'clear_drawings2')
		self.ClearDrawingsButton.clicked.connect(self.onClearDrawings)
		self.ClearDrawingsButton2.clicked.connect(self.onClearDrawings)

		# Line edits
		self.accelDeviceUpdates = self.findChild(QtWidgets.QLabel, 'accelDeviceUpdate')
		self.peakEnergyDisp = self.findChild(QtWidgets.QLabel, 'peak_energy_disp')
		self.peakFreqencyDisp = self.findChild(QtWidgets.QLabel, 'peak_frequency_disp')
		self.aucDisp = self.findChild(QtWidgets.QLabel, 'auc_disp')
		self.peakPeakDisp = self.findChild(QtWidgets.QLabel, 'peak_peak_disp')

		# List Widgets
		self.patientList = self.findChild(QtWidgets.QListView, 'prevPatientList')
		self.accelCasesList = self.findChild(QtWidgets.QListView, 'accelCases')
		self.currentAccelView = self.findChild(QtWidgets.QListView, 'current_accel_view')

		# Add all previous cases in the QListView Object
		for item in self.prev_pt_lists:
			self.patientList.addItem(item)

		# Disable Drawing
		self.spiralTab.setEnabled(False)

		self.show()

	###############################################################################################
	## Helper Functions
	###############################################################################################

	# Analyze the data
	def analyze_data(self):

		print('Starting analysis ...')

		# If no trials have been done, return
		if (len(self.accel_files) == 0):
			print('  Could not analyze. No accelerometer files.')
			return

		# Create a directory to save the analysis if it doesnt exist
		if not os.path.isdir(self.data_save_path + 'analysis'):
			os.mkdir(self.data_save_path + 'analysis')

		# Temporary arrays to determine the improvement
		peak_vals = np.array([])
		auc_welchs = np.array([])
		auc_accels = np.array([])
		f_maxs = np.array([])
		peak_peaks = np.array([])

		# Analyze the accelerometer data
		for i in range(len(self.accel_trials)):
			# Load the data
			t, x, y, z = load_data_accel(self.data_save_path + self.accel_trials[i] + '.csv')

			# Complete fourier and analysis of the data
			f, accel_welch, peak_val, auc_welch, f_max, auc_accel, peak_peak = analyze_accel_data(t, x, y, z)

			peak_vals = np.append(peak_vals, peak_val)
			auc_welchs = np.append(auc_welchs, auc_welch)
			auc_accels = np.append(auc_accels, auc_accel)
			f_maxs = np.append(f_maxs, f_max)
			peak_peaks = np.append(peak_peaks, peak_peak)

			with open(self.data_save_path + 'analysis/' + self.accel_trials[i] + '_accel_psd.csv', 'w', newline='') as file:
				writer = csv.writer(file)
				for j in range(len(f)):
					writer.writerow([f[j], accel_welch[j]])

			if self.accel_trials[i] not in self.accel_psds:
				self.accel_psds.append(self.accel_trials[i])
				fl = open(self.data_save_path + 'analysis/accel_psd_fls.csv', 'a')
				fl.write(self.accel_trials[i] + '\n')
				fl.close()

		# Collate the improvement
		all_accel_stats = np.vstack([peak_vals, auc_welchs, auc_accels, peak_peaks, f_maxs])

		# Write the improvement data to file
		with open(self.data_save_path + 'analysis/' + 'accel_analysis.csv', 'w', newline='') as file:
				writer = csv.writer(file)
				for j in range(all_accel_stats.shape[1]):
					writer.writerow([all_accel_stats[0][j], all_accel_stats[1][j], all_accel_stats[2][j], all_accel_stats[3][j], all_accel_stats[4][j]])

		print('  Done.')

		# Plot the accelerometer and the improvment plots
		self.plot_analysis()

	# Make PDF report
	def generate_pdf(self):

		# Create the PDF
		c = canvas.Canvas(self.data_save_path + self.pt_id + '_report.pdf', pagesize=letter)
		width, height = letter

		# Add the patient info
		c.setFont("Helvetica-Bold", 18)
		c.drawString(50, height - 40, self.pt_id + ' Spiral Report')
		c.setFont("Helvetica", 13)

		# Add the date info
		with open(self.basePath + self.pt_id + '.txt', 'r') as file:
			lines = file.readlines()
			date_plus_time = lines[2]

		c.drawString(50, height - 60, date_plus_time)

		# Make directory to save figure if it is not already made
		if not os.path.isdir(self.data_save_path + 'analysis/pdf_figs/'):
			os.mkdir(self.data_save_path + 'analysis/pdf_figs/')

		for i in range(len(self.accel_psds)):
			# Print the trial name on the PDF
			c.setFont("Helvetica-Bold", 13)
			c.drawString(50, height - 90, self.accel_psds[i])
			c.setFont("Helvetica", 12)

			# Save the PSD (will exist for all)
			f, psd = load_data_accel_psd(self.data_save_path + 'analysis/' + self.accel_psds[i] + '_accel_psd.csv')

			# Save the image to folder
			plt.figure()
			plt.plot(f, psd, color='b')
			plt.title(self.accel_trials[i] + ', Accelerometer PSD', fontsize=18)
			plt.xlabel('Frequency (Hz)', fontsize=14)
			plt.ylabel('PSD (G^2/Hz)', fontsize=14)
			plt.grid(True)
			plt.savefig(self.data_save_path + 'analysis/pdf_figs/' + self.accel_psds[i] + '_psd.png')
			plt.close()

			# Get the display statistics
			display_statistics = []
			with open(self.data_save_path + 'analysis/' + 'accel_analysis.csv', newline='') as csvfile:
				spiral_reader = csv.reader(csvfile, delimiter=',')
				for row in spiral_reader:
					if spiral_reader.line_num - 1 == i:
						display_statistics.append(round(float(row[0]), 3))
						display_statistics.append(round(float(row[1]), 3))
						display_statistics.append(round(float(row[3]), 3))
						display_statistics.append(float(row[4]))

			c.drawString(50, height - 110, 'Tremor (PSD) Peak: ' + str(display_statistics[0]) + ' G^2/Hz')
			c.drawString(50, height - 130, 'Peak at Frequency: ' + str(display_statistics[3]) + ' Hz')
			c.drawString(50, height - 150, 'Peak-Peak Amplitude of Accelerometer: ' + str(display_statistics[2]) + ' G')
			c.drawString(50, height - 170, 'AUC of PSD (4-12Hz): ' + str(display_statistics[1]) + ' G*Hz')

			# Add the PSD figure in
			c.drawImage(ImageReader(self.data_save_path + 'analysis/pdf_figs/' + self.accel_psds[i] + '_psd.png'), 150, height - 550, width=300, preserveAspectRatio=True, mask='auto')


			# Plot CCW spiral if it exists
			if os.path.isfile(self.data_save_path + self.accel_trials[i] + '_ccw_spiral.csv'):
				arr_pts_x, arr_pts_y = load_data_spiral(self.data_save_path + self.accel_trials[i] + '_ccw_spiral.csv')

				arr_pts_tmp_x = []
				arr_pts_tmp_y = []

				# Get the points in the current spiral
				with open(self.application_path + 'ims/ideal_ccw_spiral.csv', newline='') as csvfile:
					spiral_reader = csv.reader(csvfile, delimiter=',')
					for row in spiral_reader:
						arr_pts_tmp_x.append(int(row[1]))
						arr_pts_tmp_y.append(int(row[2]))

				# Save pngs of spiral
				plt.figure()
				plt.plot(arr_pts_tmp_x, arr_pts_tmp_y, color='r')
				plt.plot(arr_pts_x, arr_pts_y, color='b')
				plt.title(self.accel_trials[i] + ', CCW Spiral', fontsize=18)
				plt.grid(True)
				plt.savefig(self.data_save_path + 'analysis/pdf_figs/' + self.accel_psds[i] + '_ccw_spiral.png')
				plt.close()

				# Add the PSD figure in
				#c.drawImage(ImageReader(self.data_save_path + 'analysis/pdf_figs/' + self.accel_psds[i] + '_ccw_spiral.png'), 50, height - 300, width=250, preserveAspectRatio=True, mask='auto')

			# Plot CW spiral if it exists
			if os.path.isfile(self.data_save_path + self.accel_trials[i] + '_cw_spiral.csv'):
				arr_pts_x, arr_pts_y = load_data_spiral(self.data_save_path + self.accel_trials[i] + '_cw_spiral.csv')

				arr_pts_tmp_x = []
				arr_pts_tmp_y = []

				with open(self.application_path + 'ims/ideal_cw_spiral.csv', newline='') as csvfile:
					spiral_reader = csv.reader(csvfile, delimiter=',')
					for row in spiral_reader:
						arr_pts_tmp_x.append(int(row[1]))
						arr_pts_tmp_y.append(int(row[2]))

				# Save pngs of spiral
				plt.figure()
				plt.plot(arr_pts_tmp_x, arr_pts_tmp_y, color='r')
				plt.plot(arr_pts_x, arr_pts_y, color='b')
				plt.title(self.accel_trials[i] + ', CW Spiral', fontsize=18)
				plt.grid(True)
				plt.savefig(self.data_save_path + 'analysis/pdf_figs/' + self.accel_psds[i] + '_cw_spiral.png')
				plt.close()

				# Add the PSD figure in
				#c.drawImage(ImageReader(self.data_save_path + 'analysis/pdf_figs/' + self.accel_psds[i] + '_cw_spiral.png'), 310, height - 300, width=250, preserveAspectRatio=True, mask='auto')

			# Plot Line if it exists
			if os.path.isfile(self.data_save_path + self.accel_trials[i] + '_line_spiral.csv'):
				arr_pts_x, arr_pts_y = load_data_spiral(self.data_save_path + self.accel_trials[i] + '_line_spiral.csv')

				arr_pts_tmpu_x = []
				arr_pts_tmpu_y = []
				arr_pts_tmpl_x = []
				arr_pts_tmpl_y = []
				# Get the points in the current spiral
				with open(self.application_path + 'ims/line_ideal_upper.csv', newline='') as csvfile:
					spiral_reader = csv.reader(csvfile, delimiter=',')
					for row in spiral_reader:
						arr_pts_tmpu_x.append(int(row[1]))
						arr_pts_tmpu_y.append(int(row[2]))

				with open(self.application_path + 'ims/line_ideal_lower.csv', newline='') as csvfile:
					spiral_reader = csv.reader(csvfile, delimiter=',')
					for row in spiral_reader:
						arr_pts_tmpl_x.append(int(row[1]))
						arr_pts_tmpl_y.append(int(row[2]))

				# Save pngs of spiral
				plt.figure()
				plt.plot(arr_pts_tmpu_x, arr_pts_tmpu_y, color='r')
				plt.plot(arr_pts_tmpl_x, arr_pts_tmpl_y, color='r')
				plt.plot(arr_pts_x, arr_pts_y, color='b')
				plt.title(self.accel_trials[i] + ', Line', fontsize=18)
				plt.ylim(-20, 180)
				plt.grid(True)
				plt.savefig(self.data_save_path + 'analysis/pdf_figs/' + self.accel_psds[i] + '_line.png')
				plt.close()

				# Add the PSD figure in
				#c.drawImage(ImageReader(self.data_save_path + 'analysis/pdf_figs/' + self.accel_psds[i] + '_line.png'), 50, height - 500, width=250, preserveAspectRatio=True, mask='auto')

			# Print the current page
			c.showPage()

		# Save the PDF after it has been printed to
		c.save()

	# Plot according to the selected item in box
	def plot_selected(self):
		if self.currentAccelView.currentItem() is None:
			return
		else:
			if os.path.isfile(self.data_save_path + 'analysis/' + self.currentAccelView.currentItem().text() + '_accel_psd.csv'):
				self.plot_analysis(self.currentAccelView.currentIndex().row())
			else:
				self.analyze_data()
				self.plot_analysis(self.currentAccelView.currentIndex().row())


	# Plot the acelerometer data
	def plot_analysis(self, to_plot='last'):

		# If nothing to plot
		if len(self.accel_psds) == 0:
			return

		if to_plot == 'last':
			to_plot = len(self.accel_psds) - 1

		# Clear all plots
		self.clear_all_plots()

		# Plot the right accelerometer trial
		f, psd = load_data_accel_psd(self.data_save_path + 'analysis/' + self.accel_psds[to_plot] + '_accel_psd.csv')

		self.AccelPSDCanvas.axes.plot(f, psd, color='b')
		self.AccelPSDCanvas.axes.set_xlabel('Frequency (Hz)', fontsize=13)
		self.AccelPSDCanvas.axes.set_ylabel('PSD (G^2/Hz)', fontsize=13)
		self.AccelPSDCanvas.axes.set_xlim(min(f), max(f))
		self.AccelPSDCanvas.axes.set_ylim(0, max(psd) * 2)
		self.AccelPSDCanvas.axes.set_title(self.accel_trials[to_plot] + ', Accel PSD', fontsize=14)
		self.AccelPSDCanvas.axes.grid(True)
		self.AccelPSDCanvas.draw()

		display_statistics = []

		# Display the spiral statistics on the screen
		with open(self.data_save_path + 'analysis/' + 'accel_analysis.csv', newline='') as csvfile:
			spiral_reader = csv.reader(csvfile, delimiter=',')
			for row in spiral_reader:
				if spiral_reader.line_num - 1 == to_plot:
					display_statistics.append(round(float(row[0]), 3))
					display_statistics.append(round(float(row[1]), 3))
					display_statistics.append(round(float(row[3]), 3))
					display_statistics.append(float(row[4]))

		# Show the display statistics
		self.peakEnergyDisp.setText(str(display_statistics[0]))
		self.peakFreqencyDisp.setText(str(display_statistics[3]))
		self.aucDisp.setText(str(display_statistics[1]))
		self.peakPeakDisp.setText(str(display_statistics[2]))

		# Plot CCW spiral
		if os.path.isfile(self.data_save_path + self.accel_trials[to_plot] + '_ccw_spiral.csv'):
			arr_pts_x, arr_pts_y = load_data_spiral(self.data_save_path + self.accel_trials[to_plot] + '_ccw_spiral.csv')

			arr_pts_tmp_x = []
			arr_pts_tmp_y = []

			# Get the points in the current spiral
			with open(self.application_path + 'ims/ideal_ccw_spiral.csv', newline='') as csvfile:
				spiral_reader = csv.reader(csvfile, delimiter=',')
				for row in spiral_reader:
					arr_pts_tmp_x.append(int(row[1]))
					arr_pts_tmp_y.append(int(row[2]))

			# Plot the spirals
			self.SpiralCCWCanvas.clear_plot()
			self.SpiralCCWCanvas.axes.plot(arr_pts_tmp_x, arr_pts_tmp_y, color='r')
			self.SpiralCCWCanvas.draw()
			self.SpiralCCWCanvas.axes.plot(arr_pts_x, arr_pts_y, color='b')
			self.SpiralCCWCanvas.axes.set_title('CCW Spiral', fontsize=14)
			self.SpiralCCWCanvas.draw()

		# CW
		if os.path.isfile(self.data_save_path + self.accel_trials[to_plot] + '_cw_spiral.csv'):
			arr_pts_x, arr_pts_y = load_data_spiral(self.data_save_path + self.accel_trials[to_plot] + '_cw_spiral.csv')

			arr_pts_tmp_x = []
			arr_pts_tmp_y = []

			with open(self.application_path + 'ims/ideal_cw_spiral.csv', newline='') as csvfile:
				spiral_reader = csv.reader(csvfile, delimiter=',')
				for row in spiral_reader:
					arr_pts_tmp_x.append(int(row[1]))
					arr_pts_tmp_y.append(int(row[2]))

			self.SpiralCWCanvas.clear_plot()
			self.SpiralCWCanvas.axes.plot(arr_pts_tmp_x, arr_pts_tmp_y, color='r')
			self.SpiralCWCanvas.draw()
			self.SpiralCWCanvas.axes.plot(arr_pts_x, arr_pts_y, color='b')
			self.SpiralCWCanvas.axes.set_title('CW Spiral', fontsize=14)
			self.SpiralCWCanvas.draw()

		# Line
		if os.path.isfile(self.data_save_path + self.accel_trials[to_plot] + '_line_spiral.csv'):
			arr_pts_x, arr_pts_y = load_data_spiral(self.data_save_path + self.accel_trials[to_plot] + '_line_spiral.csv')

			arr_pts_tmpu_x = []
			arr_pts_tmpu_y = []
			arr_pts_tmpl_x = []
			arr_pts_tmpl_y = []
			# Get the points in the current spiral
			with open(self.application_path + 'ims/line_ideal_upper.csv', newline='') as csvfile:
				spiral_reader = csv.reader(csvfile, delimiter=',')
				for row in spiral_reader:
					arr_pts_tmpu_x.append(int(row[1]))
					arr_pts_tmpu_y.append(int(row[2]))

			with open(self.application_path + 'ims/line_ideal_lower.csv', newline='') as csvfile:
				spiral_reader = csv.reader(csvfile, delimiter=',')
				for row in spiral_reader:
					arr_pts_tmpl_x.append(int(row[1]))
					arr_pts_tmpl_y.append(int(row[2]))

			self.LineCanvas.clear_plot()
			self.LineCanvas.axes.plot(arr_pts_tmpu_x, arr_pts_tmpu_y, color='r')
			self.LineCanvas.draw()
			self.LineCanvas.axes.plot(arr_pts_tmpl_x, arr_pts_tmpl_y, color='r')
			self.LineCanvas.draw()
			self.LineCanvas.axes.plot(arr_pts_x, arr_pts_y, color='b')
			self.LineCanvas.axes.set_title('Line', fontsize=14)
			self.LineCanvas.axes.set_ylim(-10, 170)
			self.LineCanvas.draw()

	def clear_all_plots(self):
		self.AccelPSDCanvas.clear_plot()
		self.SpiralCCWCanvas.clear_plot()
		self.SpiralCWCanvas.clear_plot()
		self.LineCanvas.clear_plot()

		self.peakEnergyDisp.setText('')
		self.peakFreqencyDisp.setText('')
		self.aucDisp.setText('')
		self.peakPeakDisp.setText('')

	###############################################################################################
	## Button Click Functions
	###############################################################################################

	# Function to start the case
	def start_case(self):
		# Get the patient ID, remove all sapces from the ID
		tmp_ptid= self.patientIdEnter.text()
		tmp_ptid.replace(' ', '')
		self.prev_pt_list = next(os.walk(self.basePath))[1]

		if tmp_ptid == '' or (tmp_ptid in self.prev_pt_list):
			return
		else:
			self.aboutCaseWindow.setEnabled(True)
			self.accelControlWindow.setEnabled(True)
			self.spiralControlWindow.setEnabled(True)
			self.startCaseButton.setEnabled(False)
			self.stopCaseButton.setEnabled(True)
			self.loadCaseButton.setEnabled(False)
			self.patientIdEnter.setEnabled(False)
			self.trialNameAccelerom.setEnabled(True)
			self.downloadAccelButton.setEnabled(False)
			self.cancelRecordButton.setEnabled(False)
			self.RHRadio.setChecked(True)

			self.isNewCase = True

			# Write a txt file that stores the case
			self.pt_id = tmp_ptid
			fl = open(self.basePath + self.pt_id + '.txt', 'w')
			fl.write(self.pt_id + '\n' + self.basePath + self.pt_id + '/' + '\n' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + '\n\n')
			fl.close()
			fl = open(self.basePath + self.pt_id + '_spirals.txt', 'w')
			fl.close()
			self.data_save_path = self.basePath + self.pt_id + '/'
			os.mkdir(self.data_save_path)

	# Function to finish the case
	def finish_case(self):

		self.aboutCaseWindow.setEnabled(False)
		self.accelControlWindow.setEnabled(False)
		self.spiralControlWindow.setEnabled(False)
		self.startCaseButton.setEnabled(True)
		self.stopCaseButton.setEnabled(False)
		self.loadCaseButton.setEnabled(True)
		self.patientIdEnter.setEnabled(True)
		self.patientIdEnter.setText('')
		self.trialNameAccelerom.setText('')
		self.RHValueFeild.setValue(1)
		self.LHValueFeild.setValue(1)
		self.RHRadio.setChecked(True)

		# Add all previous cases in the QListView Object
		self.prev_pt_list = next(os.walk(self.basePath))[1]

		if self.isNewCase:
			self.patientList.addItem(self.pt_id)

		# Clear the list views
		self.accelCasesList.clear()
		self.currentAccelView.clear()

		# Write a txt file that stores the case
		self.pt_id = ''
		self.data_save_path = ''
		self.previous_spiral_ccw = ''
		self.previous_spiral_cw = ''
		self.previous_spiral_line = ''
		self.accel_files = []
		self.ccw_spirals = []
		self.cw_spirals = []
		self.line_spirals = []
		self.accel_psds = []
		self.accel_trials = []
		self.rh_current = 1
		self.lh_current = 1
		self.isNewCase = False

		self.clear_all_plots()

	# Function to load a previous case
	def load_case(self):
		# Load the patient ID, and set the class variables
		self.pt_id = self.patientList.currentItem().text()
		self.data_save_path = self.basePath + self.pt_id + '/'
		self.patientIdEnter.setText(self.pt_id)


		# Open accel files
		self.accel_files = []
		with open(self.basePath + self.pt_id + '.txt') as file:
			for line in file:
				self.accel_files.append(line.rstrip())

		# Delete header information
		del(self.accel_files[0])
		del(self.accel_files[0])
		del(self.accel_files[0])
		del(self.accel_files[0])

		# Get the accel files
		self.accel_trials = []
		for i in range(len(self.accel_files)):
			if os.path.isfile(self.basePath + self.pt_id + '/' + self.accel_files[i] + '.csv'):
				self.accel_trials.append(self.accel_files[i])

		# Get the analyzed psd files
		self.accel_psds = []
		if os.path.isfile(self.data_save_path + 'analysis/accel_psd_fls.csv'):
			# Load the analyzed psd files
			with open(self.data_save_path + 'analysis/accel_psd_fls.csv') as file:
				for line in file:
					self.accel_psds.append(line.rstrip())

		# Get the spiral files
		self.ccw_spirals = []
		self.cw_spirals = []
		self.line_spirals = []
		with open(self.basePath + self.pt_id + '_spirals.txt') as file:
			for line in file:
				if len(line.rstrip()) > 4:
					if line.rstrip()[0:3] == 'ccw':
						self.ccw_spirals.append(line.rstrip()[4:len(line.rstrip())] + '_ccw')
					elif line.rstrip()[0:2] == 'cw':
						self.cw_spirals.append(line.rstrip()[3:len(line.rstrip())] + '_cw')
					elif line.rstrip()[0:4] == 'line':
						self.line_spirals.append(line.rstrip()[5:len(line.rstrip())] + '_line')

		# Add entries to the current trials
		for item in self.accel_trials:
			self.currentAccelView.addItem(item)

		# Disable all other start case functions
		self.aboutCaseWindow.setEnabled(True)
		self.accelControlWindow.setEnabled(True)
		self.spiralControlWindow.setEnabled(True)
		self.startCaseButton.setEnabled(False)
		self.stopCaseButton.setEnabled(True)
		self.loadCaseButton.setEnabled(False)
		self.patientIdEnter.setEnabled(False)
		self.trialNameAccelerom.setEnabled(True)
		self.downloadAccelButton.setEnabled(False)
		self.cancelRecordButton.setEnabled(False)
		self.resetBoardButton.setEnabled(False)

		# Make sure RH variables are reset
		rh_fls_s = glob.glob(self.data_save_path + 'clinic_rh*_ccw_spiral.csv')
		rh_fls_a = glob.glob(self.data_save_path + 'clinic_rh*.csv')

		ii = 0
		while ii < len(rh_fls_a):
			if rh_fls_a[ii][len(rh_fls_a[ii])-10:len(rh_fls_a[ii])-4] == 'spiral':
				rh_fls_a.pop(ii)
				continue
			ii += 1

		self.rh_current = max([len(rh_fls_s), len(rh_fls_a)]) + 1
		if self.rh_current == 0 or self.rh_current > 15:
			self.rh_current = 1

		# Make sure LH variables are reset
		lh_fls_s = glob.glob(self.data_save_path + 'clinic_lh*_ccw_spiral.csv')
		lh_fls_a = glob.glob(self.data_save_path + 'clinic_lh*.csv')

		ii = 0
		while ii < len(lh_fls_a):
			if lh_fls_a[ii][len(lh_fls_a[ii])-10:len(lh_fls_a[ii])-4] == 'spiral':
				lh_fls_a.pop(ii)
				continue
			ii += 1

		self.lh_current = max([len(lh_fls_s), len(lh_fls_a)]) + 1
		if self.lh_current == 0 or self.lh_current > 15:
			self.lh_current = 1

		self.RHValueFeild.setValue(self.rh_current)
		self.LHValueFeild.setValue(self.lh_current)
		self.RHRadio.setChecked(True)

		# Add any accel trials to the case
		for item in self.accel_files:
			self.accelCasesList.addItem(item)


	# Function to start the accelerometer recording
	def record_accel(self):

		if self.RHRadio.isChecked():
			tmp_str = 'clinic_rh' + str(self.rh_current)

		elif self.LHRadio.isChecked():
			tmp_str = 'clinic_lh' + str(self.lh_current)

		elif self.otherRadioButton.isChecked():
			# Check that two trials are not named the same
			tmp_str = self.trialNameAccelerom.text()
			tmp_str.replace(' ', '')

		elif self.testRadioButton.isChecked():
			tmp_str = 'test'
		else:
			tmp_str = ''

		if tmp_str == '' or (tmp_str in self.accel_files):
			return
		else:
			self.current_trial = tmp_str

		# Set the proper BT address
		if self.penRadioButton.isChecked():
			self.accel_address = 'C5:02:6A:76:E4:5D'
		elif self.tabletRadioButton.isChecked():
			self.accel_address = 'DA:83:E6:EE:AB:BF'
		elif self.spiralOnlyRadioButton.isChecked():
			self.accel_address = ''
		else:
			self.accel_address = 'C5:02:6A:76:E4:5D'

		# Disable the record button
		self.recordAccelButton.setEnabled(False)

		# Update user thatdevice is being set up
		if not self.spiralOnlyRadioButton.isChecked():
			self.accelDeviceUpdates.setText('Connecting to device ...')
			self.accelDeviceUpdates.setStyleSheet('Color: black;')

			# Enable Drawing
			self.spiralTab.setEnabled(True)

		# Case for DRAWING ONLY
		else:
			self.accelDeviceUpdates.setText('Ready for drawing.')
			self.accelDeviceUpdates.setStyleSheet('Color: green;')

			# Enable Drawing
			self.spiralTab.setEnabled(True)

			# Save file name and disable record button (only allow download)
			self.trialNameAccelerom.setEnabled(False)
			self.recordAccelButton.setEnabled(False)
			self.downloadAccelButton.setEnabled(True)
			self.cancelRecordButton.setEnabled(True)
			self.trialNameSelect.setEnabled(False)
			self.selectDeviceGroup.setEnabled(False)
			return

		#Force GUI to update (needed due to many sleep() calls associated with BT device)
		app.processEvents()


		self.accelDevice = Accelerometer(self.accel_address, self.basePath + self.pt_id + '/' + self.current_trial + '.csv')

		# Establish connection
		connected = False
		for i in range(1):
			connected = self.accelDevice.connect()
			if connected:
				break
			else:
				self.accelDeviceUpdates.setText('Still connecting ...')
				self.accelDeviceUpdates.setStyleSheet('Color: black;')

				#Force GUI to update (needed due to many sleep() calls associated with BT device)
				app.processEvents()

				print('Trying to establish connection again...')
				sleep(1)

		if not connected:
			# Update user that device is being set up
			self.accelDeviceUpdates.setText('Could not connect. Try again.')
			self.accelDeviceUpdates.setStyleSheet('Color: red;')

			# Enable the record button
			self.recordAccelButton.setEnabled(True)

			#Force GUI to update (needed due to many sleep() calls associated with BT device)
			app.processEvents()
			return

		# Update user that device is being set up
		self.accelDeviceUpdates.setText('Connected. Setting up device ...')
		self.accelDeviceUpdates.setStyleSheet('Color: black;')

		#Force GUI to update (needed due to many sleep() calls associated with BT device)
		app.processEvents()

		isRecording = self.accelDevice.log()
		if isRecording:
			self.accelDeviceUpdates.setText('Recording ...')
			self.accelDeviceUpdates.setStyleSheet('Color: red;')

			# Save file name and disable record button (only allow download)
			self.trialNameAccelerom.setEnabled(False)
			self.recordAccelButton.setEnabled(False)
			self.downloadAccelButton.setEnabled(True)
			self.cancelRecordButton.setEnabled(True)
			self.trialNameSelect.setEnabled(False)
			self.selectDeviceGroup.setEnabled(False)
		else:
			# Enable the record button again
			self.recordAccelButton.setEnabled(True)
			print('Error in BT setup... try again')

	# Fuction to download the acclerometer recording after spiral is done
	def download_accel(self):

		# If no accelerometer used, do not download
		if self.spiralOnlyRadioButton.isChecked():

			# Get the accelerometer data and write it to file
			if self.current_trial != 'test':
				fl = open(self.basePath + self.pt_id + '.txt', 'a')
				fl.write(self.current_trial + '\n')
				fl.close()

			# Disable buttons and add trial to list
			if self.current_trial != 'test':
				self.accelCasesList.addItem(self.current_trial)
				self.accel_files.append(self.current_trial)
			self.trialNameAccelerom.setEnabled(True)
			self.recordAccelButton.setEnabled(True)
			self.downloadAccelButton.setEnabled(False)
			self.cancelRecordButton.setEnabled(False)
			self.trialNameSelect.setEnabled(True)
			if self.RHRadio.isChecked():
				self.rh_current += 1
				self.RHValueFeild.setValue(self.rh_current)
			if self.LHRadio.isChecked():
				self.lh_current += 1
				self.LHValueFeild.setValue(self.lh_current)
			self.current_trial = ''
			self.selectDeviceGroup.setEnabled(True)

			# Disable Drawing
			self.spiralTab.setEnabled(False)

			# Signal to UI that the data is being downloaded
			self.accelDeviceUpdates.setText('Done. Ready for next trial.')
			self.accelDeviceUpdates.setStyleSheet('Color: green;')

			#Force GUI to update (needed due to many sleep() calls associated with BT device)
			app.processEvents()

			print('. Done.... Ready for next trial')
			return

		# If accel was used.

		# Check to make sure device did not loose connection
		if self.accelDevice.isConnected:
			print('Downloading data...')

			# Signal to UI that the data is being downloaded
			self.accelDeviceUpdates.setText('Downloading data ...')
			self.accelDeviceUpdates.setStyleSheet('Color: green;')

			# Disable Download and cancel buttons
			self.downloadAccelButton.setEnabled(False)
			self.cancelRecordButton.setEnabled(False)

			#Force GUI to update (needed due to many sleep() calls associated with BT device)
			app.processEvents()

			#isDownloaded = self.accelDevice.stop_log(self.data_save_path + self.current_trial + '.csv')
			isDownloaded = self.accelDevice.stop_log()
		else:
			print('Connecton lost during recording... Trying to reestablish...')

			# Signal to UI that the data is being downloaded
			self.accelDeviceUpdates.setText('Reconnecting ...')
			self.accelDeviceUpdates.setStyleSheet('Color: black;')

			#Force GUI to update (needed due to many sleep() calls associated with BT device)
			app.processEvents()

			connected = False
			for i in range(2):
				connected = self.accelDevice.connect()
				if connected:
					break
				else:
					print('Trying to establish connection again...')
					sleep(1)

			# After connection, call is_downloaded function
			if self.accelDevice.isConnected:
				print('Downloading...')

				# Signal to UI that the data is being downloaded
				self.accelDeviceUpdates.setText('Downloading data ...')
				self.accelDeviceUpdates.setStyleSheet('Color: green;')

				#Force GUI to update (needed due to many sleep() calls associated with BT device)
				app.processEvents()

				#isDownloaded = self.accelDevice.stop_log(self.data_save_path + self.current_trial + '.csv')
				isDownloaded = self.accelDevice.stop_log()
			else:
				isDownloaded = False

				# Signal to UI that the data is being downloaded
				self.accelDeviceUpdates.setText('Connect failed. Try again.')
				self.accelDeviceUpdates.setStyleSheet('Color: red;')

				#Force GUI to update (needed due to many sleep() calls associated with BT device)
				app.processEvents()

				print('  Could not download. Try again.')

		if isDownloaded:
			# Signal that downloading is complete
			print('  Done')

			# Signal to UI that the data is being downloaded
			self.accelDeviceUpdates.setText('Done. Reseting BT ...')
			self.accelDeviceUpdates.setStyleSheet('Color: black;')

			#Force GUI to update (needed due to many sleep() calls associated with BT device)
			app.processEvents()

			# Get the accelerometer data and write it to file
			if self.current_trial != 'test':
				fl = open(self.basePath + self.pt_id + '.txt', 'a')
				fl.write(self.current_trial + '\n')
				fl.close()

			# Disable buttons and add trial to list
			if self.current_trial != 'test':
				self.accelCasesList.addItem(self.current_trial)
				self.accel_files.append(self.current_trial)
				self.accel_trials.append(self.current_trial)
				self.currentAccelView.addItem(self.current_trial)

			self.trialNameAccelerom.setEnabled(True)
			self.recordAccelButton.setEnabled(True)
			self.downloadAccelButton.setEnabled(False)
			self.cancelRecordButton.setEnabled(False)
			self.trialNameSelect.setEnabled(True)
			if self.RHRadio.isChecked():
				self.rh_current += 1
				self.RHValueFeild.setValue(self.rh_current)
			if self.LHRadio.isChecked():
				self.lh_current += 1
				self.LHValueFeild.setValue(self.lh_current)
			self.current_trial = ''
			self.selectDeviceGroup.setEnabled(True)

			# Disable Drawing
			self.spiralTab.setEnabled(False)

			print('Reseting ...')
			self.accelDevice.reset()

			# Signal to UI that the data is being downloaded
			self.accelDeviceUpdates.setText('Done. Ready for next trial.')
			self.accelDeviceUpdates.setStyleSheet('Color: green;')

			#Force GUI to update (needed due to many sleep() calls associated with BT device)
			app.processEvents()

			print('. Done.... Ready for next trial')

			# Analyze and plot the data
			self.analyze_data()
		else:
			# Signal to UI that the data is being downloaded
			self.accelDeviceUpdates.setText('Download failed. Try again.')
			self.accelDeviceUpdates.setStyleSheet('Color: red;')

			# Disable Download and cancel buttons
			self.downloadAccelButton.setEnabled(True)
			self.cancelRecordButton.setEnabled(True)

			#Force GUI to update (needed due to many sleep() calls associated with BT device)
			app.processEvents()

			print('Error in downloading ... try again')

	# Function to cancel the accelerometer recording button
	def cancel_accel_record(self):

		if not self.spiralOnlyRadioButton.isChecked():
			# Signal to UI that the data is being downloaded
			self.accelDeviceUpdates.setText('Cancel and Reset...')
			self.accelDeviceUpdates.setStyleSheet('Color: black;')

		# Disable Download and cancel buttons
		self.downloadAccelButton.setEnabled(False)
		self.cancelRecordButton.setEnabled(False)

		#Force GUI to update (needed due to many sleep() calls associated with BT device)
		app.processEvents()

		isCanceled = False
		if not self.spiralOnlyRadioButton.isChecked():
			isCanceled = self.accelDevice.cancel_record()

		if isCanceled or self.spiralOnlyRadioButton.isChecked():
			# Disable buttons and add trial to list
			self.trialNameAccelerom.setEnabled(True)
			self.recordAccelButton.setEnabled(True)
			self.downloadAccelButton.setEnabled(False)
			self.cancelRecordButton.setEnabled(False)
			self.trialNameSelect.setEnabled(True)
			self.selectDeviceGroup.setEnabled(True)

			# Signal to UI that the data is being downloaded
			self.accelDeviceUpdates.setText('Done. Ready for next trial.')
			self.accelDeviceUpdates.setStyleSheet('Color: green;')

			# Disable Drawing
			self.spiralTab.setEnabled(False)

			#Force GUI to update (needed due to many sleep() calls associated with BT device)
			app.processEvents()

			self.current_trial = ''
			print('Canceled')
		else:
			# Signal to UI that the data is being downloaded
			self.accelDeviceUpdates.setText('Error in Cancel. Try again.')
			self.accelDeviceUpdates.setStyleSheet('Color: red;')

			#Force GUI to update (needed due to many sleep() calls associated with BT device)
			app.processEvents()

			print('Could not cancel. Try again.')

		return

	# Function to handle reset request from user
	def handle_reset(self):
		print('Reseting BT board...')

		# Check to make sure device did not loose connection
		if self.accelDevice.isConnected:
			isReset = self.accelDevice.reset()
		else:
			print('Connecton lost ... Trying to reestablish...')
			connected = False
			for i in range(5):
				connected = self.accelDevice.connect()
				if connected:
					break
				else:
					print('Trying to establish connection again...')
					sleep(1)

			# After connection, call reset function
			if self.accelDevice.isConnected:
				print('Reseting BT board ...')
				isDownloaded = self.accelDevice.reset()
			else:
				isDownloaded = False
				print('  Could not download. Try again.')

	def onDoneCCW(self):
		if self.current_trial != '':
			file_path = self.basePath + self.pt_id + '/' + self.current_trial + '_ccw_spiral.csv'
		else:
			file_path = self.basePath + self.pt_id + '/ccw_spiral.csv'

		# Do not allow empty spirals to be saved
		if self.drawingAreaCCW.drawn_points == []:
			return

		self.drawingAreaCCW.saveDrawing(file_path)
		self.drawingAreaCCW.clearDrawing()
		self.previous_spiral_ccw = file_path
		if (self.current_trial not in self.ccw_spirals) and (self.current_trial != 'test'):
			self.ccw_spirals.append(self.current_trial + '_ccw')

		# Get the spiral name and add it to file
		if self.current_trial != 'test':
			fl = open(self.basePath + self.pt_id + '_spirals.txt', 'a')
			fl.write('ccw_' + self.current_trial + '\n')
			fl.close()

	def onDoneCW(self):
		if self.current_trial != '':
			file_path = self.basePath + self.pt_id + '/' + self.current_trial + '_cw_spiral.csv'
		else:
			file_path = self.basePath + self.pt_id + '/cw_spiral.csv'

		# Do not allow empty spirals to be saved
		if self.drawingAreaCW.drawn_points == []:
			return

		self.drawingAreaCW.saveDrawing(file_path)
		self.drawingAreaCW.clearDrawing()
		self.previous_spiral_cw = file_path
		if (self.current_trial not in self.cw_spirals) and (self.current_trial != 'test'):
			self.cw_spirals.append(self.current_trial + '_cw')

		# Get the spiral name and add it to file
		if self.current_trial != 'test':
			fl = open(self.basePath + self.pt_id + '_spirals.txt', 'a')
			fl.write('cw_' + self.current_trial + '\n')
			fl.close()

	def onDoneLine(self):
		if self.current_trial != '':
			file_path = self.basePath + self.pt_id + '/' + self.current_trial + '_line_spiral.csv'
		else:
			file_path = self.basePath + self.pt_id + '/line_spiral.csv'

		# Do not allow empty spirals to be saved
		if self.drawingAreaLine.drawn_points == []:
			return

		self.drawingAreaLine.saveDrawing(file_path)
		self.drawingAreaLine.clearDrawing()
		self.previous_spiral_line = file_path
		if (self.current_trial not in self.line_spirals) and (self.current_trial != 'test'):
			self.line_spirals.append(self.current_trial + '_line')

		# Get the spiral name and add it to file
		if self.current_trial != 'test':
			fl = open(self.basePath + self.pt_id + '_spirals.txt', 'a')
			fl.write('line_' + self.current_trial + '\n')
			fl.close()

	def onLoadPreviousCCW(self):
		if self.previous_spiral_ccw != '':
			self.drawingAreaCCW.loadDrawing(self.previous_spiral_ccw)
		else:
			return

	def onLoadPreviousCW(self):
		if self.previous_spiral_cw != '':
			self.drawingAreaCW.loadDrawing(self.previous_spiral_cw)
		else:
			return

	def onLoadPreviousLine(self):
		if self.previous_spiral_line != '':
			self.drawingAreaLine.loadDrawing(self.previous_spiral_line)
		else:
			return

	def onClearDrawings(self):
		self.drawingAreaCCW.clearDrawing()
		self.drawingAreaCW.clearDrawing()
		self.drawingAreaLine.clearDrawing()

# Start UI
window = spiralDrawSystem()
if sys.platform != 'win32':
	os.system('clear')
app.exec_()

# To do before system Exit
if sys.platform != 'win32':
	os.system('clear')
