# Key Test Cases

## AuthForm
- **Login**
  - Valid credentials (username, password)
  - Invalid username or password
  - Empty fields
  - Case sensitivity in usernames

- **Register**
  - Valid registration details
  - Existing user tries to register with same username/email
  - Empty fields
  - Weak password (e.g., less than 8 characters)

## LoginForm
- Valid login credentials
- Invalid login credentials
- Empty fields
- Case sensitivity in usernames

## RegisterForm
- Valid registration details
- Existing user tries to register with same username/email
- Empty fields
- Weak password (e.g., less than 8 characters)
- Special characters in username or email

## PatientProfile
- View patient profile by ID
- Update patient profile (name, age, gender, address)
- Delete patient profile
- Invalid patient ID

## AppointmentCalendar
- Schedule appointment
- Cancel existing appointment
- View appointments for a specific date
- No appointments available on specified date

## MedicalRecordViewer
- View medical record by ID
- Add new medical record
- Update existing medical record
- Delete medical record
- Invalid record ID

## StaffSchedule
- View staff schedule
- Generate leave request
- Approve or deny leave request
- Invalid staff ID

## LeaveRequestForm
- Submit valid leave request
- Submit invalid leave request (e.g., future date)
- Approve or deny leave request
- Invalid staff ID

## InvoiceGenerator
- Generate invoice for an appointment
- View generated invoices by ID
- Update payment status of an invoice
- Delete invoice
- Invalid invoice ID

# Edge Cases

## AuthForm
- Empty username and password fields
- Very long usernames (exceeding database constraints)
- Very long passwords (exceeding database constraints)

## LoginForm
- Very long username or email (exceeding database constraints)
- Very long password (exceeding database constraints)

## RegisterForm
- Very long username or email (exceeding database constraints)
- Very long password (exceeding database constraints)
- Special characters in username or email

## PatientProfile
- Invalid patient ID (e.g., non-existent ID)
- Empty fields for update

## AppointmentCalendar
- Schedule appointment with invalid date format
- Cancel appointment that does not exist
- View appointments on a future date

## MedicalRecordViewer
- Invalid record ID (e.g., non-existent ID)
- Add new medical record without required fields

## StaffSchedule
- Generate leave request for non-existent staff member
- Approve or deny leave request with invalid ID

## LeaveRequestForm
- Submit leave request with invalid future date
- Approve or deny leave request with invalid ID

## InvoiceGenerator
- Generate invoice for non-existent appointment
- Update payment status of non-existent invoice
- Delete non-existent invoice