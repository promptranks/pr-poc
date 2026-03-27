#!/usr/bin/env python3
"""Rebuild leaderboard Redis sorted sets from database."""

import asyncio
import sys

sys.path.insert(0, "apps/api")

from app.database import async_session, engine
from app.services.leaderboard_service import rebuild_all
from app.services.redis_client import close_redis, get_redis


async def main() -> None:
    redis = await get_redis()
    async with async_session() as db:
        stats = await rebuild_all(db, redis)
        print(f"Rebuilt leaderboard: {stats}")
    await close_redis()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
