from Accelerometer import *

# Set the address
address = 'C5:02:6A:76:E4:5D'

# Create the Accerlerometer device
accelDevice = Accelerometer(address)

# Connect the Device
isConnected = accelDevice.connect()
if isConnected:
	print("Connected to " + accelDevice.device.address)

# Reset the Device
print('Reseting...')
isReset = accelDevice.full_reset()
if isReset:
	print('  Done.')