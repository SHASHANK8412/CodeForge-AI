"""
AIForge V2 – API Documentation Generator
=========================================
Generates API_DOCUMENTATION.md documenting REST endpoints, parameters, schemas, and auth requirements.
"""

class APIDocsGenerator:

    def generate_api_docs(self, project_name: str) -> str:
        return f"""# REST API Reference Documentation – {project_name}

## Authentication Endpoints

### `POST /api/v1/auth/login`
- **Description**: Authenticates user and issues JWT Bearer token.
- **Request Body**:
  ```json
  {{
    "username": "admin",
    "password": "password123"
  }}
  ```
- **Response `200 OK`**:
  ```json
  {{
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "user": {{ "name": "Admin User" }}
  }}
  ```

### `POST /api/v1/auth/register`
- **Description**: Registers a new user account.
- **Response `201 Created`**: Returns registered user record.

## Project Management Endpoints

### `GET /api/v1/projects`
- **Description**: Returns list of user projects.
- **Headers**: `Authorization: Bearer <token>`
- **Response `200 OK`**:
  ```json
  [
    {{ "id": "p1", "name": "AI Resume Analyzer", "status": "active" }}
  ]
  ```
"""


global_api_docs = APIDocsGenerator()
