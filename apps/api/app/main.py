from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import settings
from app.database import async_session, engine
from app.models import Base
from app.routers import assessment, auth, badges, leaderboard, usage, dashboard, analytics, payments
from app.services.leaderboard_service import rebuild_all
from app.services.redis_client import close_redis, get_redis

logger = logging.getLogger(__name__)


class ExplicitCORSMiddleware(BaseHTTPMiddleware):
    """Ensure CORS headers are always present, even through Cloudflare proxy."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        origin = request.headers.get("origin")
        if origin and origin in settings.effective_cors_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Max-Age"] = "600"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup, restore leaderboard cache when empty, then clean up on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    redis = await get_redis()
    if await redis.zcard("lb:alltime") == 0:
        async with async_session() as session:
            result = await rebuild_all(session, redis)
            logger.info("Leaderboard cache rebuilt on startup", extra=result)

    yield
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="PromptRanks API",
    description="AI Prompt Engineering Assessment Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.effective_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add explicit CORS headers for Cloudflare compatibility
app.add_middleware(ExplicitCORSMiddleware)

app.include_router(assessment.router)
app.include_router(auth.router)
app.include_router(badges.router)
app.include_router(leaderboard.router)
app.include_router(usage.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(payments.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
