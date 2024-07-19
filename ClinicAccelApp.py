from Accelerometer import *
from PaintFunctions import *
from PlotFunctions import *
import os
import sys
import glob

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

		uic.loadUi('spiralDraw.ui', self)
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
		self.accel_baseline = None
		self.baseline_f_peak_val = None

		# Acclerometer
		self.accel_address = 'C5:02:6A:76:E4:5D'
		self.accelDevice = Accelerometer(self.accel_address)

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
		self.resetBoardButton.clicked.connect(self.handle_reset)
		self.PlotAccels = self.findChild(QtWidgets.QPushButton, 'plot_accel_aspects')
		#self.PlotAccels.clicked.connect(self.plot_accels)

		self.recordAccelButton = self.findChild(QtWidgets.QPushButton, 'recordAccel')
		self.recordAccelButton.clicked.connect(self.record_accel)
		self.downloadAccelButton = self.findChild(QtWidgets.QPushButton, 'downloadAccel')
		self.downloadAccelButton.clicked.connect(self.download_accel)
		self.cancelRecordButton = self.findChild(QtWidgets.QPushButton, 'cancelRecord')
		self.cancelRecordButton.clicked.connect(self.cancel_accel_record)
		self.analyzeAccelDataButton = self.findChild(QtWidgets.QPushButton, 'analyze_accel_data')
		#self.analyzeAccelDataButton.clicked.connect(self.analyze_data)


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
		self.baselineTrialLE = self.findChild(QtWidgets.QLabel, 'baseline_disp')

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
	'''
	# Function to plot sample data
	def plot_improvement(self):

		if not os.path.isfile(self.data_save_path + 'analysis/' + 'improvement_accel.csv'):
			return

		self.canvasImprove.clear_plot()

		x, improve = load_data_accel_psd(self.data_save_path + 'analysis/' + 'improvement_accel.csv')

		for i in range(len(improve)):
			improve[i] = improve[i] * 100

		self.canvasImprove.axes.plot(x, improve, marker="s", color='r')

		self.canvasImprove.axes.set_xlabel('Sonication', fontsize=13)
		self.canvasImprove.axes.set_ylabel('Tremor Reduction (%)', fontsize=13)
		self.canvasImprove.axes.set_title('Tremor Improvement', fontsize=18)
		self.canvasImprove.axes.set_xlim([min(x), max(x)])
		self.canvasImprove.axes.set_ylim([-100, 20])
		self.canvasImprove.axes.legend(['Accelerometer'])
		self.canvasImprove.axes.grid(True)
		self.canvasImprove.draw()

	# Analyze the data
	def analyze_data(self):

		print('Starting analysis ...')

		# If no trials have been done, return
		if (len(self.accel_files) == 0) or (self.accel_baseline == None):
			print('  Could not analyze. No accel files or no baseline selected.')
			return

		# Create a directory to save the analysis if it doesnt exist
		if not os.path.isdir(self.data_save_path + 'analysis'):
			os.mkdir(self.data_save_path + 'analysis')

		# Temporary arrays to determine the improvement
		peak_vals = np.array([])
		auc_welchs = np.array([])
		auc_accels = np.array([])

		# Analyze the accelerometer data
		for i in range(len(self.accel_trials)):
			# Load the data
			t, x, y, z = load_data_accel(self.data_save_path + self.accel_trials[i] + '.csv')

			# Complete fourier and analysis of the data
			f, accel_welch, peak_val, auc_welch, auc_accel = analyze_accel_data(t, x, y, z)

			peak_vals = np.append(peak_vals, peak_val)
			auc_welchs = np.append(auc_welchs, auc_welch)
			auc_accels = np.append(auc_accels, auc_accel)

			with open(self.data_save_path + 'analysis/' + self.accel_trials[i] + '_accel_psd.csv', 'w', newline='') as file:
				writer = csv.writer(file)
				for j in range(len(f)):
					writer.writerow([f[j], accel_welch[j]])

			if self.accel_trials[i] not in self.accel_psds:
				self.accel_psds.append(self.accel_trials[i])
				fl = open(self.data_save_path + 'analysis/accel_psd_fls.csv', 'a')
				fl.write(self.accel_trials[i] + '\n')
				fl.close()

		# Add the baseline trial and the maxinum value of that trial to file to easlity be acessible
		with open(self.data_save_path + 'analysis/' + 'accel_baseline_info.csv', 'w', newline='') as file:
			writer = csv.writer(file)
			writer.writerow(['BaselineIndex', self.accel_baseline])
			writer.writerow(['BaselineMaxF', peak_vals[self.accel_baseline]])

		# Save the peak val for graphing frequency
		self.baseline_f_peak_val = peak_vals[self.accel_baseline]

		# Collate the improvement
		all_accel_stats = np.vstack([peak_vals, auc_welchs, auc_accels])
		ref_vals = all_accel_stats[:, self.accel_baseline]
		improve_accel_all = all_accel_stats / ref_vals[:, None] - 1
		improve_accel = np.mean(improve_accel_all, axis=0)

		# Write the improvement data to file
		with open(self.data_save_path + 'analysis/' + 'improvement_accel.csv', 'w', newline='') as file:
				writer = csv.writer(file)
				for j in range(len(improve_accel)):
					writer.writerow([j, improve_accel[j]])
		print('  Done.')

		# Plot the accelerometer and the improvment plots
		self.plot_improvement()
		self.FreqAccelPlotRadio.setChecked(True)
		self.plot_accels()

	# Plot the acelerometer data
	def plot_accels(self):
		# Clear all plots
		self.clear_small_plots()

		# Plot the entire timeseries
		if self.RawAccelPlotRadio.isChecked():
			# Loop through all spirals drawn so far
			for i in range(len(self.accel_trials)):
				# Only 7 graphs. Cannot plot more.
				if i > 7:
					break

				t, x, y, z = load_data_accel(self.data_save_path + self.accel_trials[i] + '.csv')
				to_plot = []
				for j in range(len(x)):
					to_plot.append(x[j] + y[j] + z[j])
				eval('self.canvasGraph' + str((i+1)) + '.axes.plot(t, to_plot, color=\'b\')')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_xlabel(\'Time (s)\', fontsize=13)')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_ylabel(\'Acceleration (G)\', fontsize=13)')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_title(self.accel_trials[i] + \', Full Accel Trace\', fontsize=14)')
				eval('self.canvasGraph' + str((i+1)) + '.axes.grid(True)')
				eval('self.canvasGraph' + str((i+1)) + '.draw()')

		elif self.AccelSamplePlotRadio.isChecked():
			# Loop through all spirals drawn so far
			for i in range(len(self.accel_trials)):
				# Only 7 graphs. Cannot plot more.
				if i > 7:
					break

				t, x, y, z = load_data_accel(self.data_save_path + self.accel_trials[i] + '.csv')
				to_plot = []
				for j in range(len(x)):
					to_plot.append(x[j] + y[j] + z[j])
				if len(to_plot) > 500:
					ind_plot_min = 400
					ind_plot_max = 500
				elif len(to_plot) >= 103:
					ind_plot_min = 2
					ind_plot_max = 102
				else:
					continue

				eval('self.canvasGraph' + str((i+1)) + '.axes.plot(t[ind_plot_min:ind_plot_max], to_plot[ind_plot_min:ind_plot_max], color=\'b\')')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_xlabel(\'Time (s)\', fontsize=13)')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_ylabel(\'Acceleration (G)\', fontsize=13)')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_title(self.accel_trials[i] + \', 1s of Accel Trace\', fontsize=14)')
				eval('self.canvasGraph' + str((i+1)) + '.axes.grid(True)')
				eval('self.canvasGraph' + str((i+1)) + '.draw()')

		elif self.FreqAccelPlotRadio.isChecked():
			# Loop through all spirals drawn so far
			for i in range(len(self.accel_psds)):
				# Only 7 graphs. Cannot plot more.
				if i > 7:
					break

				f, psd = load_data_accel_psd(self.data_save_path + 'analysis/' + self.accel_psds[i] + '_accel_psd.csv')

				eval('self.canvasGraph' + str((i+1)) + '.axes.plot(f, psd, color=\'b\')')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_xlabel(\'Frequency (Hz)\', fontsize=13)')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_ylabel(\'PSD (G^2/Hz)\', fontsize=13)')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_xlim(min(f), max(f))')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_ylim(0, self.baseline_f_peak_val * 2)')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_title(self.accel_trials[i] + \', Accel PSD\', fontsize=14)')
				eval('self.canvasGraph' + str((i+1)) + '.axes.grid(True)')
				eval('self.canvasGraph' + str((i+1)) + '.draw()')


	# Plot the spiral data
	def plot_spirals(self):

		# Clear all plots
		self.clear_small_plots()

		# If want to plot CCW spiral
		if self.CCWPlotRadio.isChecked():
			# Loop through all spirals drawn so far
			for i in range(len(self.ccw_spirals)):
				# Only 7 graphs. Cannot plot more.
				if i > 7:
					break

				arr_pts_x, arr_pts_y = load_data_spiral(self.data_save_path + self.ccw_spirals[i] + '_spiral.csv')

				arr_pts_tmp_x = []
				arr_pts_tmp_y = []
				# Get the points in the current spiral
				with open(self.application_path + 'ims/ideal_ccw_spiral.csv', newline='') as csvfile:
					spiral_reader = csv.reader(csvfile, delimiter=',')
					for row in spiral_reader:
						arr_pts_tmp_x.append(int(row[1]))
						arr_pts_tmp_y.append(int(row[2]))

				# Plot the spirals
				eval('self.canvasGraph' + str((i+1)) + '.clear_plot()')
				eval('self.canvasGraph' + str((i+1)) + '.axes.plot(arr_pts_tmp_x, arr_pts_tmp_y, color=\'r\')')
				eval('self.canvasGraph' + str((i+1)) + '.draw()')
				eval('self.canvasGraph' + str((i+1)) + '.axes.plot(arr_pts_x, arr_pts_y, color=\'b\')')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_title(self.ccw_spirals[i], fontsize=14)')
				eval('self.canvasGraph' + str((i+1)) + '.draw()')

		elif self.CWPlotRadio.isChecked():
			# Loop through all spirals drawn so far
			for i in range(len(self.cw_spirals)):
				# Only 7 graphs. Cannot plot more.
				if i > 7:
					break

				arr_pts_x = []
				arr_pts_y = []
				# Get the points in the current spiral
				with open(self.data_save_path + self.cw_spirals[i] + '_spiral.csv', newline='') as csvfile:
					spiral_reader = csv.reader(csvfile, delimiter=',')
					for row in spiral_reader:
						if row[1] != 'X':
							arr_pts_x.append(int(row[1]))
							arr_pts_y.append(int(row[2]))

				arr_pts_tmp_x = []
				arr_pts_tmp_y = []
				# Get the points in the current spiral
				with open(self.application_path + 'ims/ideal_cw_spiral.csv', newline='') as csvfile:
					spiral_reader = csv.reader(csvfile, delimiter=',')
					for row in spiral_reader:
						arr_pts_tmp_x.append(int(row[1]))
						arr_pts_tmp_y.append(int(row[2]))

				# Plot the spirals
				eval('self.canvasGraph' + str((i+1)) + '.clear_plot()')
				eval('self.canvasGraph' + str((i+1)) + '.axes.plot(arr_pts_tmp_x, arr_pts_tmp_y, color=\'r\')')
				eval('self.canvasGraph' + str((i+1)) + '.draw()')
				eval('self.canvasGraph' + str((i+1)) + '.axes.plot(arr_pts_x, arr_pts_y, color=\'b\')')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_title(self.cw_spirals[i], fontsize=14)')
				eval('self.canvasGraph' + str((i+1)) + '.draw()')

		elif self.LinePlotRadio.isChecked():
			# Loop through all spirals drawn so far
			for i in range(len(self.line_spirals)):
				# Only 7 graphs. Cannot plot more.
				if i > 7:
					break

				arr_pts_x = []
				arr_pts_y = []
				# Get the points in the current spiral
				with open(self.data_save_path + self.line_spirals[i] + '_spiral.csv', newline='') as csvfile:
					spiral_reader = csv.reader(csvfile, delimiter=',')
					for row in spiral_reader:
						if row[1] != 'X':
							arr_pts_x.append(int(row[1]))
							arr_pts_y.append(int(row[2]))

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

				# Plot the spirals
				eval('self.canvasGraph' + str((i+1)) + '.clear_plot()')
				eval('self.canvasGraph' + str((i+1)) + '.axes.plot(arr_pts_tmpu_x, arr_pts_tmpu_y, color=\'r\')')
				eval('self.canvasGraph' + str((i+1)) + '.draw()')
				eval('self.canvasGraph' + str((i+1)) + '.axes.plot(arr_pts_tmpl_x, arr_pts_tmpl_y, color=\'r\')')
				eval('self.canvasGraph' + str((i+1)) + '.draw()')
				eval('self.canvasGraph' + str((i+1)) + '.axes.plot(arr_pts_x, arr_pts_y, color=\'b\')')
				eval('self.canvasGraph' + str((i+1)) + '.axes.set_title(self.line_spirals[i], fontsize=14)')
				eval('self.canvasGraph' + str((i+1)) + '.draw()')

		elif self.SFlotRadio.isChecked():
			return

	def clear_all_plots(self):
		self.canvasImprove.clear_plot()
		self.canvasGraph1.clear_plot()
		self.canvasGraph2.clear_plot()
		self.canvasGraph3.clear_plot()
		self.canvasGraph4.clear_plot()
		self.canvasGraph5.clear_plot()
		self.canvasGraph6.clear_plot()
		self.canvasGraph7.clear_plot()
		self.canvasGraph8.clear_plot()

	def clear_small_plots(self):
		self.canvasGraph1.clear_plot()
		self.canvasGraph2.clear_plot()
		self.canvasGraph3.clear_plot()
		self.canvasGraph4.clear_plot()
		self.canvasGraph5.clear_plot()
		self.canvasGraph6.clear_plot()
		self.canvasGraph7.clear_plot()
		self.canvasGraph8.clear_plot()
	'''
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
			self.preopRadioButton.setChecked(True)

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
		self.accel_baseline = None
		self.baseline_f_peak_val = None

		#self.clear_all_plots()

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
		self.accel_baseline = None
		self.baseline_f_peak_val = None
		if os.path.isdir(self.data_save_path + 'analysis'):
			# Load the analyzed psd files
			with open(self.data_save_path + 'analysis/accel_psd_fls.csv') as file:
				for line in file:
					self.accel_psds.append(line.rstrip())

			# Load the baseline info
			with open(self.data_save_path + 'analysis/' + 'accel_baseline_info.csv', newline='') as csvfile:
				c_reader = csv.reader(csvfile, delimiter=',')
				for row in c_reader:
					if row[0] == 'BaselineIndex':
						self.accel_baseline = int(row[1])
						self.baselineTrialLE.setText(self.accel_psds[self.accel_baseline])
					if row[0] == 'BaselineMaxF':
						self.baseline_f_peak_val = float(row[1])

			# Plot the accelerometer and the improvment plots
			#self.plot_improvement()

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
		print(rh_fls_s)
		print(rh_fls_a)

		ii = 0
		while ii < len(rh_fls_a):
			print(rh_fls_a[ii][len(rh_fls_a[ii])-10:len(rh_fls_a[ii])-4])
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
		print(lh_fls_s)
		print(lh_fls_a)

		ii = 0
		while ii < len(lh_fls_a):
			print(lh_fls_a[ii][len(lh_fls_a[ii])-10:len(lh_fls_a[ii])-4])
			if lh_fls_a[ii][len(lh_fls_a[ii])-10:len(lh_fls_a[ii])-4] == 'spiral':
				lh_fls_a.pop(ii)
				continue
			ii += 1

		self.lh_current = max([len(lh_fls_s), len(lh_fls_a)]) + 1
		if self.lh_current == 0 or self.lh_current > 15:
			self.lh_current = 1

		self.RHValueFeild.setValue(self.rh_current)
		self.LHValueFeild.setValue(self.lh_current)
		self.preopRadioButton.setChecked(True)

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

		self.currentSpiralsView.addItem(self.current_trial + '_ccw')

		# Get the spiral name and add it to file
		if self.current_trial != 'test':
			fl = open(self.basePath + self.pt_id + '_spirals.txt', 'a')
			fl.write('ccw_' + self.current_trial + '\n')
			fl.close()

		# Update the list views of spiral graph settings
		self.currentSpiralsView.clear()
		for item in self.ccw_spirals:
			self.currentSpiralsView.addItem(item)
		for item in self.cw_spirals:
			self.currentSpiralsView.addItem(item)
		for item in self.line_spirals:
			self.currentSpiralsView.addItem(item)

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

		# Update the list views of spiral graph settings
		self.currentSpiralsView.clear()
		for item in self.ccw_spirals:
			self.currentSpiralsView.addItem(item)
		for item in self.cw_spirals:
			self.currentSpiralsView.addItem(item)
		for item in self.line_spirals:
			self.currentSpiralsView.addItem(item)

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

		# Update the list views of spiral graph settings
		self.currentSpiralsView.clear()
		for item in self.ccw_spirals:
			self.currentSpiralsView.addItem(item)
		for item in self.cw_spirals:
			self.currentSpiralsView.addItem(item)
		for item in self.line_spirals:
			self.currentSpiralsView.addItem(item)

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
