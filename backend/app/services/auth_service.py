"""
AuthService — orchestrates registration, login, token refresh, and logout.
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.models.user_session import UserSession
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository

settings = get_settings()


def _hash_token(token: str) -> str:
    """
    We store only a SHA-256 hash of the refresh token, never the raw
    value -- a stolen DB dump then can't be used to forge sessions,
    the same principle as never storing plaintext passwords.
    """
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.audit_repo = AuditRepository(session)

    async def register(
        self, *, email: str, password: str, full_name: str, role: UserRole
    ) -> User:
        if await self.user_repo.email_exists(email):
            raise ConflictError(f"A user with email '{email}' already exists.")

        user = await self.user_repo.create(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        await self.audit_repo.log(action="USER_REGISTERED", user_id=user.id, resource_type="user", resource_id=user.id)
        return user

    async def login(
    self, *, email: str, password: str,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[str, str]:

        user = await self.user_repo.get_by_email(email)

        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")
        if not user.is_active:
            raise AuthenticationError("This account has been deactivated.")

        access_token = create_access_token(user_id=user.id, role=user.role.value)
        refresh_token = create_refresh_token(user_id=user.id)

        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_session = UserSession(
            user_id=user.id,
            refresh_token_hash=_hash_token(refresh_token),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            revoked=False,
        )
        self.session.add(new_session)
        await self.session.flush()

        await self.audit_repo.log(action="LOGIN", user_id=user.id, resource_type="user", resource_id=user.id)
        return access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> str:
        try:
            payload = decode_token(refresh_token)
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError("Refresh token has expired.") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError("Invalid refresh token.") from exc

        if payload.get("type") != TokenType.REFRESH.value:
            raise AuthenticationError("Token is not a refresh token.")

        token_hash = _hash_token(refresh_token)
        result = await self.session.execute(
            select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        )
        session_row = result.scalar_one_or_none()

        if session_row is None or session_row.revoked:
            raise AuthenticationError("Session has been revoked or does not exist.")
        if session_row.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Session has expired.")

        user = await self.user_repo.get_or_404(uuid.UUID(payload["sub"]))
        if not user.is_active:
            raise AuthenticationError("This account has been deactivated.")

        return create_access_token(user_id=user.id, role=user.role.value)

    async def logout(self, refresh_token: str) -> None:
        token_hash = _hash_token(refresh_token)
        result = await self.session.execute(
            select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        )
        session_row = result.scalar_one_or_none()
        if session_row is not None:
            session_row.revoked = True
            await self.session.flush()
            await self.audit_repo.log(action="LOGOUT", user_id=session_row.user_id)
