from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext

PWD_CONTEXT = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return PWD_CONTEXT.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return PWD_CONTEXT.verify(password, hashed)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def session_expiry(days: int = 7) -> datetime:
    return datetime.utcnow() + timedelta(days=days)
