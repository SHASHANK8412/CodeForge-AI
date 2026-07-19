# Architecture

- **Microservices Approach**: Implement as microservices to ensure modularity, scalability, and ease of maintenance.
  - User Authentication Service
  - Patient Management Service
  - Appointment Scheduling Service
  - Medical Records Service
  - Staff Management Service
  - Billing and Payment Service
  - Inventory Management Service

- **API Gateway**: Centralize API requests to manage authentication, rate limiting, and service discovery.

# Folder Structure

- `src`
  - `auth`
    - `controllers`
    - `services`
    - `models`
  - `patient`
    - `controllers`
    - `services`
    - `models`
  - `appointment`
    - `controllers`
    - `services`
    - `models`
  - `medical-record`
    - `controllers`
    - `services`
    - `models`
  - `staff`
    - `controllers`
    - `services`
    - `models`
  - `billing-payment`
    - `controllers`
    - `services`
    - `models`
  - `inventory`
    - `controllers`
    - `services`
    - `models`
- `config`
- `database`
- `tests`
- `public`
- `views`

# Database Choice

- **MongoDB**: For storing unstructured data like patient records and medical history.
- **PostgreSQL**: For structured data such as appointments, staff details, and billing information.

# API Design

- **RESTful APIs**: Use REST principles for all services.
  - `/auth/login`
  - `/auth/register`
  - `/patient/create`
  - `/appointment/schedule`
  - `/medical-record/view/:id`
  - `/staff/leave-request`
  - `/billing/invoice/generate`

- **Swagger Documentation**: Generate API documentation using Swagger to ensure clarity and ease of integration.