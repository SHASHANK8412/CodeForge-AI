# Hospital Management System

## Description

The Hospital Management System is designed to streamline hospital operations by providing comprehensive tools for patient registration, appointment scheduling, medical record keeping, staff management, billing, and inventory control. This system aims to enhance efficiency, accuracy, and patient satisfaction.

## Features

- **Patient Registration & Management**: Manage patient profiles, appointments, and medical records.
- **Appointment Scheduling & Cancellation**: Schedule and cancel appointments with ease.
- **Medical Record Keeping & Retrieval**: Maintain detailed medical histories for patients.
- **Staff Management (Scheduling, Leave, Attendance)**: Track staff schedules, leave requests, and attendance.
- **Billing & Payment Processing**: Generate invoices and process payments efficiently.
- **Inventory Management for Medical Supplies**: Monitor and manage stock levels of medical supplies.

## Installation

1. Clone the repository:
      git clone https://github.com/your-repo-url.git
   
2. Navigate to the project directory:
      cd hospital-management-system
   
3. Install dependencies:
      pip install -r requirements.txt
   
4. Set up the database (using PostgreSQL and MongoDB):
      cp config/settings.example.py config/settings.py
   # Edit settings.py with your database credentials
   python manage.py db init
   python manage.py db migrate
   python manage.py db upgrade
   
5. Run the application:
      python app.py
   
## Usage

1. **User Authentication**:
   - Register and log in using `/auth/register` and `/auth/login`.

2. **Patient Management**:
   - Create, update, or delete patient records with `/patient/create`, `/patient/update/:id`, and `/patient/delete/:id`.

3. **Appointment Scheduling**:
   - Schedule appointments with `/appointment/schedule`.
   - Cancel appointments with `/appointment/cancel/:id`.

4. **Medical Records**:
   - View medical records with `/medical-record/view/:id`.
   - Add or update medical records with `/medical-record/add/:id` and `/medical-record/update/:id`.

5. **Staff Management**:
   - Create, update, or delete staff members with `/staff/create`, `/staff/update/:id`, and `/staff/delete/:id`.
   - Submit leave requests with `/staff/leave-request`.

6. **Billing & Payment**:
   - Generate invoices with `/billing/invoice/generate`.
   - View invoices with `/billing/invoice/view/:id`.

7. **Inventory Management**:
   - List, add, update, or delete inventory items with `/inventory/list`, `/inventory/add`, `/inventory/update/:id`, and `/inventory/delete/:id`.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.