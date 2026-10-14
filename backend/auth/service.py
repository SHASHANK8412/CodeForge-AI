import json
import secrets
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from backend.auth.security import hash_password, verify_password

USERS_FILE = Path(__file__).resolve().parent.parent / "data" / "users.json"
USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

# Shared memory stores
USERS_DB: Dict[str, dict] = {}
API_KEYS_DB: Dict[str, list] = {}

# Default admin / initial user
DEFAULT_USER_ID = "usr_shashank_default"
DEFAULT_USER = {
    "id": DEFAULT_USER_ID,
    "name": "Shashank",
    "email": "user@example.com",
    "password_hash": hash_password("password123"),
    "created_at": "2026-08-09T12:00:00Z"
}


def _load_users():
    if USERS_DB:
        return
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for u in data:
                    USERS_DB[u["id"]] = u
        except Exception:
            pass

    if DEFAULT_USER_ID not in USERS_DB:
        USERS_DB[DEFAULT_USER_ID] = DEFAULT_USER
        _save_users()


def _save_users():
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(USERS_DB.values()), f, indent=2)
    except Exception:
        pass


_load_users()


def register_user(name: str, email: str, password: str) -> Optional[dict]:
    _load_users()
    email_clean = email.strip().lower()
    for u in USERS_DB.values():
        if u["email"].lower() == email_clean:
            return None

    uid = f"usr_{secrets.token_hex(6)}"
    user_data = {
        "id": uid,
        "name": name.strip(),
        "email": email_clean,
        "password_hash": hash_password(password),
        "created_at": datetime.now().isoformat()
    }
    USERS_DB[uid] = user_data
    _save_users()
    return user_data


def authenticate_user(email: str, password: str) -> Optional[dict]:
    _load_users()
    email_clean = email.strip().lower()
    for u in USERS_DB.values():
        if u["email"].lower() == email_clean:
            if verify_password(password, u["password_hash"]):
                return u
    return None


def get_user_by_id(user_id: str) -> Optional[dict]:
    _load_users()
    return USERS_DB.get(user_id)


def create_user_api_key(user_id: str, key_name: str) -> dict:
    raw_key = f"aif_{secrets.token_hex(20)}"
    key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
    key_id = f"key_{secrets.token_hex(6)}"

    key_record = {
        "id": key_id,
        "user_id": user_id,
        "name": key_name,
        "key_hash": key_hash,
        "key_preview": f"aif_{raw_key[4:8]}••••••••••••••••",
        "raw_key": raw_key,
        "created_at": datetime.now().strftime("%b %d, %Y")
    }

    if user_id not in API_KEYS_DB:
        API_KEYS_DB[user_id] = []
    API_KEYS_DB[user_id].append(key_record)

    return key_record


def get_user_api_keys(user_id: str) -> List[dict]:
    return API_KEYS_DB.get(user_id, [])


def revoke_user_api_key(user_id: str, key_id: str) -> bool:
    if user_id in API_KEYS_DB:
        API_KEYS_DB[user_id] = [k for k in API_KEYS_DB[user_id] if k["id"] != key_id]
        return True
    return False
