"""Shared test fixtures for the API test suite."""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.models import Base
from app.models.user import User
from app.models.question import Question
from app.database import get_db
from app.main import app


# Use SQLite for tests (no PostgreSQL needed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for all tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    """Create a test database engine."""
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)

    # SQLite doesn't enforce foreign keys by default
    @event.listens_for(eng.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """Create a test database session."""
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine):
    """Create a FastAPI test client with overridden DB dependency."""
    from httpx import AsyncClient, ASGITransport

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a basic persisted user for tests that need one."""
    user = User(
        id=uuid.uuid4(),
        email="fixture-user@test.com",
        name="Fixture User",
        password_hash="hashed",
        subscription_tier="free",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def seeded_db(db_session):
    """Seed test database with sample questions (6 per pillar = 30 total)."""
    questions = []
    for pillar in ["P", "E", "C", "M", "A"]:
        for diff in [1, 1, 2, 2, 3, 3]:
            q = Question(
                id=uuid.uuid4(),
                external_id=f"{pillar}-TEST-{diff}-{len(questions)}",
                pillar=pillar,
                difficulty=diff,
                question_type="mcq",
                question_text=f"Test question {pillar}-{diff}-{len(questions)}",
                options=["Option A", "Option B", "Option C", "Option D"],
                correct_answer=0,  # First option is always correct in tests
                explanation=f"Explanation for {pillar}-{diff}",
                tags=["test"],
                is_active=True,
            )
            db_session.add(q)
            questions.append(q)

    await db_session.commit()
    return questions


@pytest_asyncio.fixture
async def seeded_client(engine, seeded_db):
    """Test client with seeded database."""
    from httpx import AsyncClient, ASGITransport

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
