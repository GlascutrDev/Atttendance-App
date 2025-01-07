from collections import defaultdict

import requests
from datetime import datetime
from requests.auth import HTTPDigestAuth
import json
import frappe
from frappe import _
from hrms.hr.doctype.employee_checkin.employee_checkin import add_log_based_on_employee_field


class Attendance:
    def __init__(self, device_ip, major, minor, device_user, device_password):
        """
        Initializes the device configuration for attendance fetching.

        This constructor sets up the necessary parameters to connect to the attendance device
        and defines default values for certain attributes.

        Parameters:
            device_ip (str): The IP address of the device to connect to.
            major (int): Major version of the device firmware (used for compatibility checks).
            minor (int): Minor version of the device firmware (used for compatibility checks).
            device_user (str): Username for authenticating with the device.
            device_password (str): Password for authenticating with the device.

        Attributes:
            device_ip (str): Stores the device's IP address.
            attendance_depth (int): The number of days of attendance to fetch by default (set to 30).
            major (int): Stores the major firmware version.
            minor (int): Stores the minor firmware version.
            device_user (str): Stores the username for device authentication.
            device_user_password (str): Stores the password for device authentication.
        """
        self.device_ip = device_ip
        self.attendance_depth = 30
        self.major = int(major)
        self.minor = int(minor)
        self.device_user = device_user
        self.device_user_password = device_password

    def _format_time(self, time_obj):
        """
        Helper function to format a datetime object or string into the device-required format.

        The function ensures that the input is converted into a properly formatted string
        that matches the device's expected datetime format. If the input is a string,
        it is first parsed into a `datetime` object.

        Parameters:
            time_obj (datetime or str): A `datetime` object or an ISO 8601 formatted string
                                        (e.g., '2025-01-07T12:34:56Z').

        Returns:
            str: The formatted datetime string in the format 'YYYY-MM-DDTHH:MM:SS+06:00'.

        Raises:
            ValueError: If the string input is not in a valid ISO 8601 format.

        Notes:
            - The time zone offset is hardcoded to '+06:00'.
            - If the input string includes a 'Z' (indicating UTC), it is replaced with '+00:00'
              before parsing.

        Example:
            _input_: '2025-01-07T12:34:56Z'
            _output_: '2025-01-07T12:34:56+06:00'
        """
        if isinstance(time_obj, str):
            time_obj = datetime.fromisoformat(time_obj.replace("Z", "+00:00"))
        return time_obj.strftime("%Y-%m-%dT%H:%M:%S") + "+06:00"

    def fetch_all_attendance_logs(self, start_time, end_time):
        """
            Fetch all attendance logs from the device, handling pagination.

            This method retrieves attendance logs from a device using its API.
            It handles pagination by iteratively fetching data in batches based on the
            maximum results allowed per request (`self.attendance_depth`).

            Parameters:
                start_time (str): The start time for fetching logs in the format 'YYYY-MM-DDTHH:MM:SS+06:00'.
                end_time (str): The end time for fetching logs in the format 'YYYY-MM-DDTHH:MM:SS+06:00'.

            Returns:
                list: A list of all attendance records fetched from the device.

            Attributes Accessed:
                - `self.device_ip`: Device IP address.
                - `self.attendance_depth`: Maximum number of results per request.
                - `self.major` and `self.minor`: Event types to filter the results.
                - `self.device_user` and `self.device_user_password`: Credentials for device authentication.

            Raises:
                requests.exceptions.RequestException: If there is a network-related error during API communication.
                HTTPError: If the API responds with a 4xx or 5xx status code.

            Notes:
                - Uses HTTP Digest Authentication (`HTTPDigestAuth`) for secure API communication.
                - Stops fetching further data once all matches are retrieved or if an error occurs.
                - Logs are fetched in JSON format and returned as a list of dictionaries.

            Example:
                _input_:
                    start_time = '2025-01-07T00:00:00+06:00'
                    end_time = '2025-01-07T23:59:59+06:00'
                _output_:
                    [
                        {"cardNo": "12345", "eventTime": "2025-01-07T12:00:00+06:00", ...},
                        {"cardNo": "67890", "eventTime": "2025-01-07T12:05:00+06:00", ...},
                        ...
                    ]
            """
        url = f"http://{self.device_ip}/ISAPI/AccessControl/AcsEvent?format=json"
        headers = {'Content-Type': 'application/json'}

        all_records = []
        search_result_position = 0
        max_results = self.attendance_depth

        while True:
            payload = {
                "AcsEventCond": {
                    "searchID": "1",
                    "searchResultPosition": search_result_position,
                    "maxResults": max_results,
                    "major": self.major,
                    "minor": self.minor,
                    "startTime": start_time,
                    "endTime": end_time
                }
            }

            try:
                response = requests.post(
                    url,
                    data=json.dumps(payload),
                    headers=headers,
                    auth=HTTPDigestAuth(self.device_user, self.device_user_password)
                )

                response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
                data = response.json()

                if "AcsEvent" in data:
                    total_matches = data["AcsEvent"].get("totalMatches", 0)

                    if "InfoList" in data["AcsEvent"]:
                        info_list = data["AcsEvent"]["InfoList"]
                        all_records.extend(info_list)

                    # Update the search result position for the next request
                    search_result_position += max_results

                    # Stop if we have retrieved all matches
                    if search_result_position >= total_matches:
                        break
                else:
                    break

            except requests.exceptions.RequestException as e:
                break

        return all_records

    def get_employee_by_device_id(self, employee_no_string):
        """
        Fetch employee details based on the attendance device ID.

        This method queries the database to find an employee record that matches the
        given `attendance_device_id`. If no matching record is found, it logs a message.
        If found, it returns the employee details.

        Parameters:
            employee_no_string (str): The attendance device ID of the employee to search for.

        Returns:
            dict or None: A dictionary containing the employee details
            (`name` and `employee_name`) if found, or `None` if no match is found.

        Example:
            _input_: employee_no_string = "EMP123"
            _output_: {"name": "EMP-001", "employee_name": "John Doe"}

        Notes:
            - The `attendance_device_id` field must be unique for each employee in the system.
            - Logs a message to the console if no employee is found or if an employee is found.
        """
        employee = frappe.db.get_value(
            "Employee",
            {"attendance_device_id": employee_no_string},
            ["name", "employee_name"],
            as_dict=True
        )
        if not employee:
            print(f"No employee found for device ID: {employee_no_string}")
        else:
            print(f"Found employee {employee}")
        return employee

    def process_logs(self, data):
        """
        Process attendance logs and push each valid record to the Employee Checkin.

        This method filters the incoming logs, extracts necessary information, and logs
        the attendance check-in data for employees. It also updates the `last_sync_of_checkin`
        field for all shift types to the current timestamp.

        Parameters:
            data (list): A list of attendance records fetched from the device. Each record
                         should be a dictionary containing attendance details.

        Returns:
            None

        Steps:
            1. Filters out logs without the `employeeNoString` field.
            2. For each valid log:
               - Fetches the corresponding employee using `attendance_device_id`.
               - Skips processing if the employee is not found.
               - Parses and formats the timestamp.
               - Logs the check-in data using `log_employee_attendance`.
            3. Updates the `last_sync_of_checkin` field for all shift types to the current timestamp.

        Raises:
            ValueError: If the `data` parameter is not a list.

        Notes:
            - Logs are skipped if they lack a timestamp or an `employeeNoString`.
            - Timestamps are converted from ISO 8601 format to `YYYY-MM-DD HH:MM:SS`.
            - Database changes are committed after updating the shift types.

        Example:
            _input_:
                data = [
                    {
                        "employeeNoString": "EMP123",
                        "time": "2025-01-07T09:00:00Z",
                        ...
                    },
                    ...
                ]
            _output_: None
        """
        if not data:
            print("Invalid data received from Device.")
            return

        # Filter logs containing the `employeeNoString` field
        filtered_info_list = [item for item in data if "employeeNoString" in item]

        for record in filtered_info_list:
            employee_no_string = record["employeeNoString"]

            # Fetch employee using `attendance_device_id`
            employee = self.get_employee_by_device_id(employee_no_string)
            if not employee:
                continue

            emp_no = employee['name']

            # Extract and format timestamp
            timestamp = record.get("time", "")
            if not timestamp:
                continue  # Skip if no timestamp

            # Parse the timestamp (adjust if needed)
            timestamp_obj = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            formatted_timestamp = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")

            # Log the check-in data
            self.log_employee_attendance(emp_no, record, formatted_timestamp)

        # Update `last_sync_of_checkin` for all shift types
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shift_types = frappe.get_all("Shift Type", fields=["name"])
        for shift_type in shift_types:
            frappe.db.set_value("Shift Type", shift_type["name"], "last_sync_of_checkin", now)
        frappe.db.commit()

    def log_employee_attendance(self, emp_no, record, formatted_timestamp):
        """
        Log employee IN and OUT times based on individual attendance records.

        This method ensures duplicate check-ins are avoided and logs valid attendance
        records to the Employee Checkin table.

        Parameters:
            emp_no (str): The employee number (typically the primary key in the Employee table).
            record (dict): The attendance record containing details like `employeeNoString`.
            formatted_timestamp (str): The timestamp of the attendance record in the format
                                       `YYYY-MM-DD HH:MM:SS`.

        Returns:
            None

        Steps:
            1. Checks if a duplicate check-in exists for the given employee and timestamp.
            2. If no duplicate is found:
               - Logs the check-in record to the Employee Checkin table using
                 `add_log_based_on_employee_field`.
            3. If a duplicate is found, skips logging and prints a message.

        Example:
            _input_:
                emp_no = "EMP-001"
                record = {
                    "employeeNoString": "EMP123",
                    ...
                }
                formatted_timestamp = "2025-01-07 09:00:00"
            _output_: None

        Notes:
            - Duplicate detection is done using `check_duplicate_checkin`.
            - Logs are added via the `add_log_based_on_employee_field` method.
        """
        # Check for duplicate check-ins with the same timestamp
        if not self.check_duplicate_checkin(emp_no, formatted_timestamp):
            # Push the record to Employee Checkin table
            add_log_based_on_employee_field(
                employee_field_value=emp_no,
                timestamp=formatted_timestamp,
                employee_fieldname="name",
                device_id=record['employeeNoString']
            )
        else:
            print(f"Duplicate check-in found for {emp_no} at {formatted_timestamp}. Skipping log.")

    def check_duplicate_checkin(self, emp_no, timestamp):
        """
        Check if an Employee Checkin record exists for the given employee and timestamp.

        This method queries the database to determine if a check-in record already exists
        for the specified employee and timestamp. It helps prevent duplicate entries in
        the Employee Checkin table.

        Parameters:
            emp_no (str): The employee number (primary key or unique identifier in the Employee table).
            timestamp (str): The check-in timestamp in the format `YYYY-MM-DD HH:MM:SS`.

        Returns:
            bool: `True` if a duplicate record exists, `False` otherwise.

        Example:
            _input_: emp_no = "EMP-001", timestamp = "2025-01-07 09:00:00"
            _output_: True

        Notes:
            - This method relies on the `frappe.db.exists` function to check for duplicates.
            - Ensures data integrity by avoiding duplicate check-ins for the same time.

        """
        existing_checkin = frappe.db.exists(
            "Employee Checkin",
            {
                "employee": emp_no,
                "time": timestamp
            }
        )
        return existing_checkin

    def get_and_process_attendance(self, start_time, end_time):
        """
        Main method to fetch and process attendance logs.

        This method fetches attendance logs from the device using the provided start
        and end times, processes the logs to extract relevant attendance information,
        and logs the check-ins and check-outs for employees.

        Parameters:
            start_time (str or datetime): The start time for fetching the attendance logs.
            end_time (str or datetime): The end time for fetching the attendance logs.

        Returns:
            None

        Steps:
            1. Converts `start_time` and `end_time` to the required device format using
               `_format_time`.
            2. Fetches all attendance logs using `fetch_all_attendance_logs`.
            3. If logs are fetched, processes them using `process_logs`.

        Example:
            _input_:
                start_time = "2025-01-01T00:00:00Z"
                end_time = "2025-01-07T23:59:59Z"
            _output_: None

        Notes:
            - `start_time` and `end_time` should be in a format compatible with the device's
              expected timestamp format.
            - The method calls `process_logs` after retrieving and verifying the data.
        """
        data = self.fetch_all_attendance_logs(self._format_time(start_time),
                                              self._format_time(end_time))
        if data:
            self.process_logs(data)


@frappe.whitelist()
def process_attendance_in_background(start_date, end_date, device_ip, major, minor, device_user,
                                     device_user_password):
	"""
	Process attendance logs in the background for a specified date range.

	This method initializes the `Attendance` class with the provided parameters,
	fetches attendance logs from the device, and processes the logs to update
	the Employee Checkin table.

	Parameters:
		start_date (str): The start date for fetching the attendance logs in the
						  format `YYYY-MM-DD`.
		end_date (str): The end date for fetching the attendance logs in the
						format `YYYY-MM-DD`.
		device_ip (str): The IP address of the attendance device.
		major (str): The major version of the attendance device.
		minor (str): The minor version of the attendance device.
		device_user (str): The username to authenticate with the device.
		device_user_password (str): The password to authenticate with the device.

	Returns:
		None

	Steps:
		1. Initializes the `Attendance` object with the given parameters.
		2. Calls the `get_and_process_attendance` method on the `Attendance` object
		   to fetch and process logs for the specified date range.

	Example:
		_input_:
			start_date = "2025-01-01"
			end_date = "2025-01-07"
			device_ip = "192.168.1.100"
			major = "1"
			minor = "0"
			device_user = "admin"
			device_user_password = "password"
		_output_: None

	Notes:
		- This method is decorated with `@frappe.whitelist()` to allow it to be
		  called from the client-side via Frappe's whitelisted methods.
	"""
	# Initialize Attendance and start processing
	attendance = Attendance(
		device_ip=device_ip,
		major=major,
		minor=minor,
		device_user=device_user,
		device_password=device_user_password
	)
	attendance.get_and_process_attendance(start_date, end_date)

