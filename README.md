## Attendance App

A robust integration system that connects attendance devices to automate log fetching, employee mapping, and real-time attendance updates in Frappe. The app fetches attendance logs from devices, processes the logs, and maps them to employees in the system. It handles duplicate check-ins, ensures data accuracy, and streamlines HR attendance processes. The app also provides functionality for fetching attendance logs in the background and supports device configurations for multiple devices.

### Features

- **Device Configuration Management**: Allows configuration of multiple attendance devices with device IP, user credentials, and device version (major/minor).
- **Automatic Attendance Fetching**: Fetch attendance logs from devices for a specified date range.
- **Employee Mapping**: Maps attendance data to employees based on device IDs, ensuring accurate records.
- **Duplicate Check-in Prevention**: Checks for duplicate check-ins using a combination of employee ID and timestamp.
- **Real-time Updates**: Processes attendance logs in real-time, updating the Employee Check-in table as soon as logs are fetched.
- **Background Processing**: Fetch attendance logs in the background for long-running operations, ensuring smooth user experience.
- **Shift Synchronization**: Synchronizes the last check-in time for all shift types to ensure proper tracking.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO
bench install-app attendance_sync
```

### How it works

- **Device Configuration**:  
  The app fetches all device configurations from the Frappe system, which include device IP, user credentials, and device version information (major/minor).

- **Fetching Attendance Logs**:  
  The app allows the user to specify a date range (start and end date), and fetches logs from all configured devices using the device’s API.

- **Employee Mapping**:  
  For each attendance log, the app uses the device ID to map the log to the corresponding employee in the system. It ensures that no check-ins are missed by mapping the logs correctly.

- **Log Processing and Check-in**:  
  The app processes attendance logs, checking for duplicates based on the employee ID and timestamp. If the log is valid, it is added to the Employee Check-in table in Frappe. Otherwise, duplicate logs are skipped.

- **Background Task for Attendance Fetching**:  
  The app uses background tasks for long-running operations, such as fetching and processing attendance logs. This ensures the system remains responsive and does not block other tasks.

- **Real-time Updates**:  
  Once attendance logs are fetched and processed, real-time updates are made to the HR system, ensuring accuracy in attendance records for all employees.


### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/attendance_sync
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade
- 
### License

This app is licensed under the AGPL-3.0 license.

This description should provide a clearer understanding of the app’s purpose, functionality, and usage. If you have any questions or need further assistance, feel free to contact the developers or refer to the documentation.

