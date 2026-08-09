import hmac
import hashlib
import json
import base64
import time
import secrets
from typing import Optional

SECRET_KEY = "aiforge_jwt_super_secret_production_key_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 86400 * 7  # 7 days


def hash_password(password: str) -> str:
    """Hashes password securely using HMAC-SHA256 with a random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored salt$hash string."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 2:
            return False
        salt, expected_hash = parts[0], parts[1]
        key = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return hmac.compare_digest(key.hex(), expected_hash)
    except Exception:
        return False


def _b64_encode(data_bytes: bytes) -> str:
    return base64.urlsafe_b64encode(data_bytes).decode('utf-8').rstrip('=')


def _b64_decode(data_str: str) -> bytes:
    padding = 4 - (len(data_str) % 4)
    if padding != 4:
        data_str += '=' * padding
    return base64.urlsafe_b64decode(data_str)


def create_access_token(data: dict, expires_delta_seconds: Optional[int] = None) -> str:
    """Creates a JWT access token signed with SECRET_KEY."""
    to_encode = data.copy()
    expire = time.time() + (expires_delta_seconds or ACCESS_TOKEN_EXPIRE_SECONDS)
    to_encode["exp"] = int(expire)

    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_b64 = _b64_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(to_encode, separators=(',', ':')).encode('utf-8'))

    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts[0], parts[1], parts[2]

        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()

        if not hmac.compare_digest(_b64_encode(expected_sig), signature_b64):
            return None

        payload_json = _b64_decode(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)

        if payload.get("exp") and time.time() > payload["exp"]:
            return None

        return payload
    except Exception:
        return None
