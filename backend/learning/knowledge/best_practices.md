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
