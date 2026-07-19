# API Endpoints

- **User Authentication Module**
  - `POST /auth/login`
  - `POST /auth/register`

- **Patient Management Module**
  - `POST /patient/create`
  - `GET /patient/list`
  - `PUT /patient/update/:id`
  - `DELETE /patient/delete/:id`

- **Appointment Scheduling Module**
  - `POST /appointment/schedule`
  - `GET /appointment/list`
  - `PUT /appointment/cancel/:id`

- **Medical Records Module**
  - `GET /medical-record/view/:id`
  - `POST /medical-record/add/:id`
  - `PUT /medical-record/update/:id`

- **Staff Management Module**
  - `POST /staff/create`
  - `GET /staff/list`
  - `PUT /staff/update/:id`
  - `DELETE /staff/delete/:id`
  - `POST /staff/leave-request`

- **Billing and Payment Module**
  - `POST /billing/invoice/generate`
  - `GET /billing/invoice/view/:id`

- **Inventory Management Module**
  - `GET /inventory/list`
  - `POST /inventory/add`
  - `PUT /inventory/update/:id`
  - `DELETE /inventory/delete/:id`

# Folder Structure

src
├── auth
│   ├── controllers
│   │   └── auth_controller.py
│   ├── services
│   │   └── auth_service.py
│   └── models
│       └── user_model.py
├── patient
│   ├── controllers
│   │   └── patient_controller.py
│   ├── services
│   │   └── patient_service.py
│   └── models
│       └── patient_model.py
├── appointment
│   ├── controllers
│   │   └── appointment_controller.py
│   ├── services
│   │   └── appointment_service.py
│   └── models
│       └── appointment_model.py
├── medical-record
│   ├── controllers
│   │   └── medical_record_controller.py
│   ├── services
│   │   └── medical_record_service.py
│   └── models
│       └── medical_record_model.py
├── staff
│   ├── controllers
│   │   └── staff_controller.py
│   ├── services
│   │   └── staff_service.py
│   └── models
│       └── staff_model.py
├── billing-payment
│   ├── controllers
│   │   └── billing_payment_controller.py
│   ├── services
│   │   └── billing_payment_service.py
│   └── models
│       └── invoice_model.py
├── inventory
│   ├── controllers
│   │   └── inventory_controller.py
│   ├── services
│   │   └── inventory_service.py
│   └── models
│       └── item_model.py
├── config
│   └── settings.py
├── database
│   └── db.py
├── tests
│   ├── auth
│   ├── patient
│   ├── appointment
│   ├── medical-record
│   ├── staff
│   ├── billing-payment
│   └── inventory
└── public
    └── views

# Models

- **User Model**
    from pydantic import BaseModel

  class User(BaseModel):
      id: int
      username: str
      email: str
      password: str
  
- **Patient Model**
    from pydantic import BaseModel

  class Patient(BaseModel):
      id: int
      name: str
      age: int
      gender: str
      address: str
  
- **Appointment Model**
    from pydantic import BaseModel

  class Appointment(BaseModel):
      id: int
      patient_id: int
      doctor_id: int
      date_time: str
      status: str
  
- **Medical Record Model**
    from pydantic import BaseModel

  class MedicalRecord(BaseModel):
      id: int
      patient_id: int
      description: str
      date_created: str
  
- **Staff Model**
    from pydantic import BaseModel

  class Staff(BaseModel):
      id: int
      name: str
      position: str
      department: str
      leave_status: str
  
- **Invoice Model**
    from pydantic import BaseModel

  class Invoice(BaseModel):
      id: int
      patient_id: int
      total_amount: float
      payment_date: str
      status: str
  
- **Item Model**
    from pydantic import BaseModel

  class Item(BaseModel):
      id: int
      name: str
      quantity: int
      price: float