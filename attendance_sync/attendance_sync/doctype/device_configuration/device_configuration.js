// Copyright (c) 2024, GLASCUTR Limited and contributors
// For license information, please see license.txt



/**
 * Client-side script for the "Device Configuration" Doctype in Frappe.
 *
 * Adds a custom button to the form for fetching attendance data from a device.
 * When clicked, it opens a dialog to input start and end dates,
 * and then calls a server-side method to fetch the attendance data.
 *
 * Features:
 * - Displays a dialog with input fields for start and end dates.
 * - Sends the input data along with device configuration details to the server.
 * - Shows success or failure messages based on the server response.
 *
 * Usage:
 * Include this script in the client-side JavaScript file for the "Device Configuration" Doctype.
 * Ensure that the server-side method is defined and accessible at the specified path.
 */
frappe.ui.form.on("Device Configuration", {
	refresh(frm) {
		// Add a custom button to the form
		frm.add_custom_button(__('Fetch Check-in'), function () {
			// Create a dialog for fetching attendance
			let d = new frappe.ui.Dialog({
				title: __('Fetch Attendance'),
				fields: [
					{
						fieldname: 'start_date',
						label: __('Start Date'),
						fieldtype: 'Datetime',
						reqd: 1
					},
					{
						fieldname: 'end_date',
						label: __('End Date'),
						fieldtype: 'Datetime',
						reqd: 1
					}
				],
				primary_action_label: __('Fetch'),
				primary_action(values) {
					// Call the server-side method to fetch attendance
					frappe.call({
						method: 'attendance_sync.attendance_sync.doctype.device_configuration.device_configuration.fetch_attendance',
						args: {
							start_date: values.start_date,
							end_date: values.end_date,
							device_ip: frm.doc.device_ip,
							major: frm.doc.major,
							minor: frm.doc.minor,
							device_user: frm.doc.device_user,
							device_user_password: frm.doc.device_user_password
						},
						callback: function (r) {
							if (r.message) {
								frappe.msgprint(__('Attendance data fetched successfully.'));
							} else {
								frappe.msgprint(__('Failed to fetch attendance data.'));
							}
						}
					});
					// Close the dialog after submitting
					d.hide();
				}
			});
			// Show the dialog
			d.show();
		}).addClass('btn-primary');
	}
});
