"""FastAPI dependencies — authentication, authorization, DB session."""

from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import decode_access_token
from app.core.database import get_db
from app.core.errors import AuthenticationError, AuthorizationError, NotFoundError
from app.models.patient import Patient
from app.models.user import User


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid authorization header.")
    token = authorization[7:]
    user_id = decode_access_token(token)
    if user_id is None:
        raise AuthenticationError("Invalid or expired token.")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthenticationError("User not found or inactive.")
    return user


async def authorize_patient_access(
    patient_id: int,
    user: User,
    db: AsyncSession,
) -> Patient:
    """Verify user owns the patient record. Raises AuthorizationError if not."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if patient is None:
        raise NotFoundError("Patient not found.")
    if patient.owner_user_id != user.id:
        raise AuthorizationError("You do not have access to this patient.")
    return patient
