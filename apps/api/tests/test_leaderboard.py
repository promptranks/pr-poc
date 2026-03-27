"""Tests for leaderboard service functions and endpoints."""

import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.services.leaderboard_service import get_display_name, get_period_key


# ---------------------------------------------------------------------------
# Unit tests: get_display_name
# ---------------------------------------------------------------------------


def test_display_name_full():
    assert get_display_name("John Doe") == "John D."


def test_display_name_single():
    assert get_display_name("Alice") == "Alice"


def test_display_name_empty():
    assert get_display_name("") == "Anonymous"


def test_display_name_none_like():
    assert get_display_name("  ") == "Anonymous"


def test_display_name_three_parts():
    # Only first name + first initial of second word
    assert get_display_name("Mary Jane Watson") == "Mary J."


# ---------------------------------------------------------------------------
# Unit tests: get_period_key
# ---------------------------------------------------------------------------


def test_period_key_alltime():
    assert get_period_key("alltime") == "lb:alltime"


def test_period_key_unknown_defaults_to_alltime():
    assert get_period_key("bogus") == "lb:alltime"


def test_period_key_weekly():
    d = date(2025, 1, 6)  # ISO week 2 of 2025
    key = get_period_key("weekly", d)
    assert key.startswith("lb:weekly:2025:")


def test_period_key_monthly():
    d = date(2025, 3, 15)
    assert get_period_key("monthly", d) == "lb:monthly:2025:03"


def test_period_key_quarterly():
    d = date(2025, 5, 1)  # Q2
    assert get_period_key("quarterly", d) == "lb:quarterly:2025:2"
    d2 = date(2025, 1, 1)  # Q1
    assert get_period_key("quarterly", d2) == "lb:quarterly:2025:1"


# ---------------------------------------------------------------------------
# Endpoint tests using a fake Redis
# ---------------------------------------------------------------------------


class FakeRedis:
    """Minimal in-memory Redis stand-in for endpoint tests."""

    def __init__(self):
        self._zsets: dict[str, dict[str, float]] = {}
        self._strings: dict[str, str] = {}

    def pipeline(self):
        return FakePipeline(self)

    async def zrevrange(self, key, start, stop, withscores=False):
        items = sorted(
            self._zsets.get(key, {}).items(), key=lambda x: x[1], reverse=True
        )
        sliced = items[start : stop + 1]
        if withscores:
            return [(k, v) for k, v in sliced]
        return [k for k, _ in sliced]

    async def zcard(self, key):
        return len(self._zsets.get(key, {}))

    async def zrevrank(self, key, member):
        items = sorted(
            self._zsets.get(key, {}).items(), key=lambda x: x[1], reverse=True
        )
        for idx, (k, _) in enumerate(items):
            if k == member:
                return idx
        return None

    async def zscore(self, key, member):
        return self._zsets.get(key, {}).get(member)

    async def get(self, key):
        return self._strings.get(key)

    async def setex(self, key, ttl, value):
        self._strings[key] = value

    async def set(self, key, value):
        self._strings[key] = value

    async def scan(self, cursor, match=None, count=None):
        return ("0", [])

    async def delete(self, *keys):
        for k in keys:
            self._zsets.pop(k, None)
            self._strings.pop(k, None)

    def zadd_gt(self, key, mapping):
        zset = self._zsets.setdefault(key, {})
        for member, score in mapping.items():
            if member not in zset or score > zset[member]:
                zset[member] = score


class FakePipeline:
    def __init__(self, redis: FakeRedis):
        self._redis = redis
        self._ops: list = []

    def zadd(self, key, mapping, gt=False):
        self._ops.append(("zadd", key, mapping, gt))
        return self

    def setex(self, key, ttl, value):
        self._ops.append(("setex", key, ttl, value))
        return self

    def zrevrange(self, key, start, stop, withscores=False):
        self._ops.append(("zrevrange", key, start, stop, withscores))
        return self

    def zcard(self, key):
        self._ops.append(("zcard", key))
        return self

    def zrevrank(self, key, member):
        self._ops.append(("zrevrank", key, member))
        return self

    def zscore(self, key, member):
        self._ops.append(("zscore", key, member))
        return self

    async def execute(self):
        results = []
        for op in self._ops:
            if op[0] == "zadd":
                _, key, mapping, gt = op
                if gt:
                    self._redis.zadd_gt(key, mapping)
                else:
                    self._redis._zsets.setdefault(key, {}).update(mapping)
                results.append(None)
            elif op[0] == "setex":
                _, key, ttl, value = op
                self._redis._strings[key] = value
                results.append(None)
            elif op[0] == "zrevrange":
                _, key, start, stop, withscores = op
                items = sorted(
                    self._redis._zsets.get(key, {}).items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
                sliced = items[start : stop + 1]
                results.append([(k, v) for k, v in sliced] if withscores else [k for k, _ in sliced])
            elif op[0] == "zcard":
                _, key = op
                results.append(len(self._redis._zsets.get(key, {})))
            elif op[0] == "zrevrank":
                _, key, member = op
                items = sorted(
                    self._redis._zsets.get(key, {}).items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
                rank = next((i for i, (k, _) in enumerate(items) if k == member), None)
                results.append(rank)
            elif op[0] == "zscore":
                _, key, member = op
                results.append(self._redis._zsets.get(key, {}).get(member))
            else:
                results.append(None)
        return results


@pytest.mark.asyncio
async def test_get_leaderboard_empty():
    from app.services.leaderboard_service import get_leaderboard

    redis = FakeRedis()
    result = await get_leaderboard(redis)
    assert result["entries"] == []
    assert result["total"] == 0
    assert result["page"] == 1


@pytest.mark.asyncio
async def test_get_leaderboard_with_entries():
    from app.services.leaderboard_service import get_leaderboard, update_score

    redis = FakeRedis()
    await update_score(
        redis,
        user_id="user-1",
        score=85.0,
        user_name="Alice Smith",
        level=4,
        level_name="Expert",
        pillar_scores={"P": 80.0},
        badge_id="badge-1",
        achieved_at="2025-01-01T00:00:00",
    )
    await update_score(
        redis,
        user_id="user-2",
        score=72.0,
        user_name="Bob Jones",
        level=3,
        level_name="Proficient",
        pillar_scores={"P": 70.0},
        badge_id=None,
        achieved_at="2025-01-02T00:00:00",
    )

    result = await get_leaderboard(redis, period="alltime")
    assert result["total"] == 2
    entries = result["entries"]
    assert entries[0]["rank"] == 1
    assert entries[0]["score"] == 85.0
    assert entries[0]["display_name"] == "Alice S."
    assert entries[1]["rank"] == 2
    assert entries[1]["score"] == 72.0


@pytest.mark.asyncio
async def test_get_leaderboard_gt_semantics():
    """Score should only improve, never decrease."""
    from app.services.leaderboard_service import get_leaderboard, update_score

    redis = FakeRedis()
    await update_score(
        redis, "user-1", 90.0, "Alice Smith", 4, "Expert", {}, None, "2025-01-01"
    )
    # Try to post a lower score
    await update_score(
        redis, "user-1", 60.0, "Alice Smith", 3, "Proficient", {}, None, "2025-01-02"
    )
    result = await get_leaderboard(redis)
    assert result["entries"][0]["score"] == 90.0


@pytest.mark.asyncio
async def test_get_user_rank():
    from app.services.leaderboard_service import get_user_rank, update_score

    redis = FakeRedis()
    await update_score(redis, "a", 95.0, "Top User", 5, "Master", {}, None, "2025-01-01")
    await update_score(redis, "b", 80.0, "Second", 4, "Expert", {}, None, "2025-01-01")

    rank_a = await get_user_rank(redis, "a")
    assert rank_a is not None
    assert rank_a["rank"] == 1
    assert rank_a["score"] == 95.0
    assert rank_a["total"] == 2

    rank_b = await get_user_rank(redis, "b")
    assert rank_b is not None
    assert rank_b["rank"] == 2

    rank_missing = await get_user_rank(redis, "nobody")
    assert rank_missing is None


# ---------------------------------------------------------------------------
# Endpoint integration tests (no real Redis required)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_leaderboard_endpoint_no_auth(client):
    """GET /leaderboard returns 200 (or 503 if Redis down, both acceptable)."""
    with patch(
        "app.routers.leaderboard.get_redis", new_callable=AsyncMock
    ) as mock_get_redis:
        fake = FakeRedis()
        mock_get_redis.return_value = fake
        response = await client.get("/leaderboard/")
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert "entries" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_leaderboard_me_requires_auth(client):
    """GET /leaderboard/me without token returns 403 or 401."""
    response = await client.get("/leaderboard/me")
    assert response.status_code in (401, 403)
