"""Auth service: password hashing (bcrypt), JWT token creation/verification."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import bcrypt
from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User

# JWT config
ALGORITHM = "HS256"

# Bcrypt 72-byte limit
BCRYPT_MAX_BYTES = 72


def validate_password_length(password: str) -> None:
    """Validate password doesn't exceed bcrypt's 72-byte limit."""
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Password exceeds maximum length ({BCRYPT_MAX_BYTES} bytes)",
        )


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    validate_password_length(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: UUID, email: str) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Look up a user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, name: str, password: str) -> User:
    """Create a new user with bcrypt-hashed password."""
    import uuid

    validate_password_length(password)
    password_hash = hash_password(password)

    user = User(
        id=uuid.uuid4(),
        email=email,
        name=name,
        password_hash=password_hash,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
