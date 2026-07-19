# SQL Schema

-- PostgreSQL Schema for Hospital Management System

-- Tables

CREATE TABLE staff (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,
    hire_date DATE NOT NULL
);

CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender CHAR(1),
    address TEXT,
    phone_number VARCHAR(20)
);

CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(id),
    staff_id INT REFERENCES staff(id),
    appointment_date TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending'
);

CREATE TABLE medical_records (
    id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(id),
    doctor_id INT REFERENCES staff(id),
    date_of_visit DATE NOT NULL,
    diagnosis TEXT,
    treatment_notes TEXT
);

CREATE TABLE billing_invoices (
    id SERIAL PRIMARY KEY,
    appointment_id INT REFERENCES appointments(id),
    total_amount NUMERIC(10, 2) NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'Pending'
);

CREATE TABLE inventory_items (
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    price NUMERIC(10, 2) NOT NULL
);

# Relationships

- **One-to-One**: `staff` and `medical_records` (one staff member can have one medical record)
- **One-to-Many**:
  - `staff` and `appointments` (one staff member can handle multiple appointments)
  - `patients` and `appointments` (one patient can have multiple appointments)
  - `patients` and `medical_records` (one patient can have multiple medical records)
  - `appointments` and `billing_invoices` (one appointment can generate one billing invoice)
- **Many-to-One**: 
  - `inventory_items` and `staff` (one staff member can manage inventory items)

This schema provides a basic structure for the Hospital Management System, with relationships that support the core functionalities of patient management, appointment scheduling, medical records, staff management, billing, and inventory.