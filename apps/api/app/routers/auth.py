"""Auth router: register, login endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import (
    create_access_token,
    create_user,
    get_user_by_email,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# --- Request/Response schemas ---


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class RegisterResponse(BaseModel):
    id: str
    email: str
    name: str
    token: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    id: str
    email: str
    name: str
    token: str


# --- Endpoints ---


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """Register a new user with email and password."""
    # Check if email already exists
    existing = await get_user_by_email(db, body.email)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Validate password minimum length
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = await create_user(db, body.email, body.name, body.password)
    token = create_access_token(user.id, user.email)

    return RegisterResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        token=token,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Login and receive JWT token."""
    user = await get_user_by_email(db, body.email)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id, user.email)

    return LoginResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        token=token,
    )
