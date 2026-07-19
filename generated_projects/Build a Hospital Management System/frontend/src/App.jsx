# Components

- `AuthForm`
- `LoginForm`
- `RegisterForm`
- `PatientProfile`
- `AppointmentCalendar`
- `MedicalRecordViewer`
- `StaffSchedule`
- `LeaveRequestForm`
- `InvoiceGenerator`

# Folder Structure

src/
├── auth/
│   ├── components/
│   │   ├── LoginForm.js
│   │   └── RegisterForm.js
│   ├── controllers/
│   │   └── AuthController.js
│   ├── services/
│   │   └── AuthService.js
│   └── routes.js
├── patient/
│   ├── components/
│   │   └── PatientProfile.js
│   ├── controllers/
│   │   └── PatientController.js
│   ├── services/
│   │   └── PatientService.js
│   └── routes.js
├── appointment/
│   ├── components/
│   │   └── AppointmentCalendar.js
│   ├── controllers/
│   │   └── AppointmentController.js
│   ├── services/
│   │   └── AppointmentService.js
│   └── routes.js
├── medical-record/
│   ├── components/
│   │   └── MedicalRecordViewer.js
│   ├── controllers/
│   │   └── MedicalRecordController.js
│   ├── services/
│   │   └── MedicalRecordService.js
│   └── routes.js
├── staff/
│   ├── components/
│   │   └── StaffSchedule.js
│   ├── controllers/
│   │   └── StaffController.js
│   ├── services/
│   │   └── StaffService.js
│   └── routes.js
├── billing-payment/
│   ├── components/
│   │   └── InvoiceGenerator.js
│   ├── controllers/
│   │   └── BillingPaymentController.js
│   ├── services/
│   │   └── BillingPaymentService.js
│   └── routes.js
├── inventory/
│   ├── components/
│   ├── controllers/
│   ├── services/
│   └── routes.js
├── config/
│   └── database.js
├── database/
│   ├── models/
│   │   ├── User.js
│   │   ├── Patient.js
│   │   ├── Appointment.js
│   │   ├── MedicalRecord.js
│   │   ├── Staff.js
│   │   ├── Invoice.js
│   │   └── InventoryItem.js
├── tests/
│   ├── auth/
│   ├── patient/
│   ├── appointment/
│   ├── medical-record/
│   ├── staff/
│   ├── billing-payment/
│   └── inventory/
└── public/
    └── index.html

# Routing

- `/auth/login`
- `/auth/register`
- `/patient/profile/:id`
- `/appointment/schedule`
- `/medical-record/view/:id`
- `/staff/schedule`
- `/billing/invoice/generate`