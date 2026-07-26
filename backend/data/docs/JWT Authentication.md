# JWT Authentication Best Practices

## Overview
JSON Web Tokens (JWT) are an open standard (RFC 7519) for securely transmitting information between parties as a JSON object.

## Guidelines
1. **Secret Management**: Store JWT secrets in environment variables (`JWT_SECRET_KEY`). Never hardcode secrets in source files.
2. **Algorithm**: Use `HS256` for symmetric signing or `RS256` for asymmetric key pairs. Always specify `algorithms=["HS256"]` during decoding.
3. **Expiration**: Always include an `exp` (expiration time) claim (e.g. 15-60 minutes for access tokens, 7 days for refresh tokens).
4. **FastAPI Integration**: Use `OAuth2PasswordBearer` and `Depends(get_current_user)` middleware for route protection.
