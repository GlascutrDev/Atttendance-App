# Copyright (c) 2024, GLASCUTR Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DeviceConfiguration(Document):
	pass


@frappe.whitelist()
def fetch_attendance(start_date, end_date, device_ip, major, minor, device_user,
					 device_user_password):
	"""
	Queues the process to fetch attendance data from a biometric device or similar source.

	This function uses the Frappe enqueue system to run the attendance fetching process in the background,
	allowing the user to continue working without waiting for the process to complete.

	Parameters:
		start_date (str): The start date for fetching attendance data in YYYY-MM-DD format.
		end_date (str): The end date for fetching attendance data in YYYY-MM-DD format.
		device_ip (str): The IP address of the device from which attendance data is fetched.
		major (int): Major version of the device firmware (used for compatibility checks).
		minor (int): Minor version of the device firmware (used for compatibility checks).
		device_user (str): Username for authenticating with the attendance device.
		device_user_password (str): Password for authenticating with the attendance device.

	Returns:
		str: A message indicating that the attendance fetch process has been queued.

	Raises:
		frappe.ValidationError: If any validation is required before queuing the process.
		frappe.exceptions.QueueError: If there is an issue with queuing the task.

	Usage:
		Call this method from the client-side using Frappe's `frappe.call` API or directly
		as an endpoint in a custom script.

	Example:
		frappe.call({
			method: "path.to.fetch_attendance",
			args: {
				"start_date": "2025-01-01",
				"end_date": "2025-01-31",
				"device_ip": "192.168.1.100",
				"major": 2,
				"minor": 0,
				"device_user": "admin",
				"device_user_password": "password123"
			},
			callback: function(response) {
				console.log(response.message);
			}
		});
	"""
	# Queue the attendance fetching process
	frappe.enqueue(
		'attendance_sync.attendance_sync.Attendance.process_attendance_in_background',
		start_date=start_date,
		end_date=end_date,
		device_ip=device_ip,
		major=major,
		minor=minor,
		device_user=device_user,
		device_user_password=device_user_password,
		queue='long',
		timeout=3000
	)
	frappe.msgprint(_("Attendance fetching has been queued."))
	return "Attendance fetch process has been queued."
