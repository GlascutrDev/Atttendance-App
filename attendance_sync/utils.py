import frappe
from datetime import datetime
from attendance_sync.attendance_sync.Attendance import Attendance

def get_attendance_from_device():
	"""
	Fetch and process attendance logs for all devices configured in the system.

	This method retrieves all device configuration documents from the Frappe system,
	loops through each configuration, and processes attendance logs for the current day
	(00:00:00 to 23:59:59) for each device.

	Steps:
		1. Fetches all Device Configuration documents from the Frappe database.
		2. Sets the current date as the start and end time range for fetching attendance logs.
		3. Loops through each device configuration, creating an instance of the `Attendance` class
		   for each device.
		4. Calls the `get_and_process_attendance` method to fetch and process the attendance logs
		   for each device.

	Parameters:
		None

	Returns:
		None

	Example:
		_input_: None
		_output_: None (Attendance logs are processed and added to the Employee Checkin table)

	Notes:
		- The method processes attendance logs for the current day (from midnight to 11:59 PM).
		- It assumes the presence of valid `Device Configuration` documents in the system.
	"""
	# Fetch all Device Configuration documents
	device_configurations = frappe.get_all('Device Configuration',
										   fields=['device_ip', 'major', 'minor', 'device_user',
												   'device_user_password'])

	# Get the current time
	now = datetime.now()
	start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
	end_time = now.replace(hour=23, minute=59, second=59, microsecond=0)

	# Loop through each device configuration
	for device in device_configurations:
		# Create an instance of the Attendance class for each device
		attendance = Attendance(
			device_ip=device.device_ip,
			major=device.major,
			minor=device.minor,
			device_user=device.device_user,
			device_password=device.device_user_password
		)
		# Process the attendance for the given device
		attendance.get_and_process_attendance(start_time, end_time)
