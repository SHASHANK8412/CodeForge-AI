# Security Vulnerability Audit
- SQL Injection: Critical (backend/routes/auth.py:24)
- Hardcoded Secret: High (SECRET_KEY='123456')
- Wildcard CORS: Medium (allow_origins=['*'])
