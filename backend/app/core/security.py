"""
Security primitives — password hashing and JWT encode/decode.
"""

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(plain_password: str) -> str:
    print("\n" + "=" * 70)
    print("PASSWORD VALUE :", repr(plain_password))
    print("TYPE           :", type(plain_password))
    print("LENGTH         :", len(plain_password))
    print("=" * 70 + "\n")

    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    print("\n----- VERIFY PASSWORD -----")
    print("Plain Password :", repr(plain_password))
    print("Hash :", hashed_password)

    result = pwd_context.verify(plain_password, hashed_password)

    print("Verification Result :", result)
    print("---------------------------\n")

    return result


def create_access_token(*, user_id: uuid.UUID, role: str) -> str:
    return _create_token(
        subject=str(user_id),
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"role": role},
    )


def create_refresh_token(*, user_id: uuid.UUID) -> str:
    return _create_token(
        subject=str(user_id),
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def _create_token(
    *,
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),  # unique per token, used for session-hash lookups
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Raises `jwt.ExpiredSignatureError` or `jwt.InvalidTokenError` on
    failure — callers (auth dependency, auth service) are responsible
    for translating those into the app's own AuthenticationError.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
