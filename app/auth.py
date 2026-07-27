"""
Auth core: hashování hesel + JWT tokeny.

SECRET_KEY čte se z env proměnné JWT_SECRET_KEY (viz DEVLOG.md sekce 10 -
závislosti). Pro lokální vývoj má fallback, pro produkci MUSÍ být nastavena
v prostředí.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt, JWTError

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-only-insecure-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hodin

# Poznámka (v1): používáme knihovnu `bcrypt` přímo místo passlib.CryptContext
# - passlib 1.7.4 má nekompatibilitu s novějším bcrypt (4.x/5.x) backendem,
#   viz DEVLOG.md sekce 8 (rozhodnutí).
_BCRYPT_MAX_BYTES = 72  # bcrypt limit


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    pw_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(pw_bytes, password_hash.encode("utf-8"))


def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
