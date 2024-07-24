from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from scipy.signal import butter, lfilter, freqz, welch, find_peaks
import csv

class MplCanvas(FigureCanvas):
	def __init__(self, parent=None, width=5, height=4, dpi=100):
		self.fig = Figure(figsize=(width, height), dpi=dpi)
		self.axes = self.fig.add_subplot(111)
		super(MplCanvas, self).__init__(self.fig)

	def clear_plot(self):
		self.fig.clf()
		self.axes = self.fig.add_subplot(111)
		self.draw()


# Smooth a timeseries
def smooth(y, box_pts):
	box = np.ones(box_pts)/box_pts
	y_smooth = np.convolve(y, box, mode='same')
	return y_smooth

# Function to read data from a file
def load_data_spiral(fpath):
	x = []
	y = []

	# Get the points in the current spiral
	with open(fpath, newline='') as csvfile:
		spiral_reader = csv.reader(csvfile, delimiter=',')
		for row in spiral_reader:
			if row[1] != 'X':
				x.append(int(row[1]))
				y.append(int(row[2]))

	return x, y

# Function to read data from a file
def load_data_accel(fpath):
	t = []
	x = []
	y = []
	z = []
	# Get the points in the current spiral
	with open(fpath, newline='') as csvfile:
		spiral_reader = csv.reader(csvfile, delimiter=',')
		for row in spiral_reader:
			t.append(float(row[0]))
			x.append(float(row[1]))
			y.append(float(row[2]))
			z.append(float(row[3]))

	return t, x, y, z

# Function to read data from a file
def load_data_accel_psd(fpath):
	f = []
	psd = []

	# Get the points in the current spiral
	with open(fpath, newline='') as csvfile:
		spiral_reader = csv.reader(csvfile, delimiter=',')
		for row in spiral_reader:
			f.append(float(row[0]))
			psd.append(float(row[1]))

	return f, psd

# Function to analyze functions
def analyze_accel_data(t_pa, x_pa, y_pa, z_pa):

	# Turn into numpy arrays
	t = np.array(t_pa)
	x = np.array(x_pa)
	y = np.array(y_pa)
	z = np.array(z_pa)
	accel_data = x + y + z

	# Set parameters
	fs = 100
	low_f = 3
	high_f = 14
	order = 4

	# Filter the data
	b, a = butter(order, [low_f, high_f], fs=fs, btype='band')
	accel_data_filt = lfilter(b, a, accel_data)

	f_filt, welch_accel_filt = welch(accel_data_filt, fs=fs, nperseg=len(accel_data_filt)//8, noverlap=(len(accel_data_filt)//8)//2)

	box_len = int(len(welch_accel_filt)*0.03)
	if box_len == 0:
		box_len = 1
	welch_accel_filt_sm = smooth(welch_accel_filt, box_len)

	# Take the regio of interest
	idx = f_filt < 13
	f_filt_ret = f_filt[idx]
	welch_accel_ret = welch_accel_filt_sm[idx]

	# Get statstics of accel trace
	peak_val = round(max(welch_accel_ret), 5)
	auc_welch = round(np.trapz(welch_accel_ret), 5)
	auc_accel = round(np.trapz(abs(accel_data_filt)) / len(accel_data_filt), 5)
	f_max = round(f_filt_ret[np.argmax(welch_accel_ret)], 3)

	# Get P-P Amplitude
	max_pks = find_peaks(accel_data_filt)
	tst, _ = find_peaks(np.negative(accel_data_filt))
	print(tst)
	print(find_peaks(np.negative(accel_data_filt)))
	min_pks = np.negative(find_peaks(np.negative(accel_data_filt)))
	peak_peak = round(np.mean(max_pks - min_pks), 5)

	return f_filt_ret, welch_accel_ret, peak_val, auc_welch, f_max, auc_accel, peak_peak









