# AIForge Engineering Best Practices

Master guidelines compiled from successful project builds.

## 1. Folder Structure Conventions
* Organize components under `frontend/src/components/` and routing controllers in `backend/routes/`.
* Maintain a clean test suite under `tests/`.

## 2. API Design & Security
* Design asynchronous route endpoints using standard FastAPI views.
* Enforce JWT validation policies on all administrative interfaces.

## 3. Testing Strategy
* Run automated verification scans with pytest prior to compiling builds.

## Project Insight: Blog
* **Framework Stack**: React, FastAPI
* **Folder Layout**: Always separate routes., Keep frontend modular.
* **Security Protocols**: Use JWT middleware.
* **API Schema**: Always use DTOs.
* **Score**: 92%

## Project Insight: Blog
* **Framework Stack**: React, FastAPI
* **Folder Layout**: Always separate routes., Keep frontend modular.
* **Security Protocols**: Use JWT middleware.
* **API Schema**: Always use DTOs.
* **Score**: 92%

* Always enforce Pydantic v2 schemas and input sanitization headers.
