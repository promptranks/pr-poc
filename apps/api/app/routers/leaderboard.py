"""Leaderboard router: public rankings with optional auth for personal rank."""

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from jose import JWTError, jwt

from app.config import settings
from app.database import get_db
from app.middleware.auth import get_current_user
from app.services.leaderboard_service import get_leaderboard, get_user_summary
from app.services.redis_client import get_redis

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

ALGORITHM = "HS256"


def _extract_user_id(authorization: str | None) -> str | None:
    """Optionally parse Bearer JWT and return user_id (sub), or None on failure."""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    try:
        payload = jwt.decode(parts[1], settings.secret_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


@router.get("/")
async def get_leaderboard_endpoint(
    period: str = Query(default="alltime"),
    industry_id: str = Query(default=""),
    role_id: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Public leaderboard. Logged-in users see their rank highlighted."""
    try:
        redis = await get_redis()
        data = await get_leaderboard(
            redis,
            period=period,
            industry_id=industry_id,
            role_id=role_id,
            page=page,
            page_size=page_size,
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Leaderboard service unavailable")

    # Optionally identify the calling user
    user_id = _extract_user_id(authorization)
    my_rank: dict[str, Any] | None = None
    if user_id:
        for entry in data["entries"]:
            if entry["user_id"] == user_id:
                my_rank = {"rank": entry["rank"], "score": entry["score"]}
                break

    return {**data, "my_rank": my_rank}


@router.get("/me")
async def get_my_rank(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
) -> dict[str, Any]:
    """Authenticated endpoint: returns user's rank across all periods + nearby entries."""
    try:
        redis = await get_redis()
        summary = await get_user_summary(redis, str(current_user.id))
    except Exception:
        raise HTTPException(status_code=503, detail="Leaderboard service unavailable")

    return {"user_id": str(current_user.id), **summary}
