"""Auth router: register, login endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import uuid
import logging

from app.database import get_db
from app.services.auth_service import (
    create_access_token,
    create_user,
    get_user_by_email,
    verify_password,
)
from app.services.oauth_service import OAuthService
from app.services.magic_link_service import MagicLinkService
from app.services.email_service import EmailService
from app.models.assessment import Assessment

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


# --- Helper functions ---


async def _transfer_assessment_to_user(db: AsyncSession, assessment_id: str, user_id: uuid.UUID) -> None:
    """Transfer an anonymous assessment to a user account."""
    try:
        aid = uuid.UUID(assessment_id)
    except ValueError:
        logger.warning(f"Invalid assessment_id in OAuth state: {assessment_id}")
        return

    result = await db.execute(select(Assessment).where(Assessment.id == aid))
    assessment = result.scalar_one_or_none()

    if assessment and assessment.user_id is None:
        assessment.user_id = user_id
        await db.commit()
        logger.info(f"Transferred assessment {assessment_id} to user {user_id}")


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


class MagicLinkRequest(BaseModel):
    email: str


class MagicLinkResponse(BaseModel):
    message: str


class OAuthCallbackResponse(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: str | None
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

    EmailService.send_welcome_email(user.email, user.name)

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


@router.get("/google")
async def google_oauth(assessment_id: str | None = Query(None)):
    """Redirect to Google OAuth. Optionally pass assessment_id to claim after login."""
    state = secrets.token_urlsafe(16)
    if assessment_id:
        state = f"{state}:{assessment_id}"
    auth_url = OAuthService.get_google_auth_url(state)
    return RedirectResponse(auth_url)


@router.get("/google/callback", response_model=OAuthCallbackResponse)
async def google_callback(
    code: str = Query(...),
    state: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback. Claims assessment if assessment_id in state."""
    oauth_data = await OAuthService.exchange_google_code(code)
    user = await OAuthService.get_or_create_user(db, "google", oauth_data)
    token = create_access_token(user.id, user.email)

    # Check if state contains assessment_id to claim
    if state and ":" in state:
        _, assessment_id = state.split(":", 1)
        await _transfer_assessment_to_user(db, assessment_id, user.id)

    return OAuthCallbackResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        token=token,
    )


@router.get("/github")
async def github_oauth(assessment_id: str | None = Query(None)):
    """Redirect to GitHub OAuth. Optionally pass assessment_id to claim after login."""
    state = secrets.token_urlsafe(16)
    if assessment_id:
        state = f"{state}:{assessment_id}"
    auth_url = OAuthService.get_github_auth_url(state)
    return RedirectResponse(auth_url)


@router.get("/github/callback", response_model=OAuthCallbackResponse)
async def github_callback(
    code: str = Query(...),
    state: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback. Claims assessment if assessment_id in state."""
    oauth_data = await OAuthService.exchange_github_code(code)
    user = await OAuthService.get_or_create_user(db, "github", oauth_data)
    token = create_access_token(user.id, user.email)

    # Check if state contains assessment_id to claim
    if state and ":" in state:
        _, assessment_id = state.split(":", 1)
        await _transfer_assessment_to_user(db, assessment_id, user.id)

    return OAuthCallbackResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        token=token,
    )


@router.post("/magic-link", response_model=MagicLinkResponse)
async def send_magic_link(
    body: MagicLinkRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send magic link to email."""
    token = await MagicLinkService.create_magic_link(db, body.email)
    return MagicLinkResponse(message="Check your email")


@router.get("/magic-link/verify", response_model=OAuthCallbackResponse)
async def verify_magic_link(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Verify magic link and login."""
    try:
        user = await MagicLinkService.verify_magic_link(db, token)
        access_token = create_access_token(user.id, user.email)

        return OAuthCallbackResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            token=access_token,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
