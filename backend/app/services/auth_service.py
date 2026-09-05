"""Auth service — registration, login."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token, hash_password, verify_password
from app.core.errors import AuthenticationError, ConflictError, ValidationError
from app.models.user import User


async def register_user(email: str, password: str, db: AsyncSession) -> tuple[User, str]:
    """Register a new user. Returns (user, access_token)."""
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise ConflictError("An account with this email already exists. Please sign in.")

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters.")

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    await db.flush()
    token = create_access_token(user.id)
    return user, token


async def login_user(email: str, password: str, db: AsyncSession) -> tuple[User, str]:
    """Authenticate user. Returns (user, access_token)."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationError("No account found with this email. Please register first.")
    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Incorrect password. Please try again.")
    if not user.is_active:
        raise AuthenticationError("Account is disabled.")
    token = create_access_token(user.id)
    return user, token
