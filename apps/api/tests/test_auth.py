"""Unit tests for Sprint 4: Auth + Badge Claim.

Tests:
- Register: creates user with bcrypt hash, returns JWT
- Register: duplicate email returns 409
- Register: short password returns 400
- Register: bcrypt 72-byte limit enforced
- Login: valid credentials return JWT
- Login: wrong password returns 401
- Login: unknown email returns 401
- JWT: decode valid token
- JWT: decode expired/invalid token raises
- Password hashing: bcrypt roundtrip
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.services.auth_service import (
    BCRYPT_MAX_BYTES,
    create_access_token,
    decode_access_token,
    hash_password,
    validate_password_length,
    verify_password,
)


# ============================================================
# Password hashing tests
# ============================================================


def test_hash_password_roundtrip():
    """Bcrypt hash + verify roundtrip works."""
    pw = "secure_password_123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert hashed.startswith("$2b$")
    assert verify_password(pw, hashed)


def test_verify_wrong_password():
    """Wrong password fails verification."""
    hashed = hash_password("correct_password")
    assert not verify_password("wrong_password", hashed)


def test_bcrypt_72_byte_limit():
    """Password exceeding 72 bytes is rejected."""
    # 73 ASCII chars = 73 bytes
    long_pw = "a" * 73
    with pytest.raises(Exception) as exc_info:
        validate_password_length(long_pw)
    assert "72 bytes" in str(exc_info.value.detail)


def test_bcrypt_72_byte_limit_exact():
    """Password at exactly 72 bytes is accepted."""
    pw = "a" * 72
    hashed = hash_password(pw)
    assert verify_password(pw, hashed)


def test_bcrypt_multibyte_limit():
    """Multi-byte characters counted by byte length, not char length."""
    # Each CJK char is 3 bytes in UTF-8. 24 chars * 3 = 72 bytes = OK
    pw_ok = "\u4e00" * 24  # 72 bytes
    hashed = hash_password(pw_ok)
    assert verify_password(pw_ok, hashed)

    # 25 chars * 3 = 75 bytes = too long
    pw_long = "\u4e00" * 25
    with pytest.raises(Exception):
        validate_password_length(pw_long)


# ============================================================
# JWT tests
# ============================================================


def test_create_and_decode_token():
    """JWT create and decode roundtrip."""
    user_id = uuid.uuid4()
    email = "test@example.com"
    token = create_access_token(user_id, email)

    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["email"] == email


def test_decode_invalid_token():
    """Invalid JWT raises 401."""
    with pytest.raises(Exception) as exc_info:
        decode_access_token("not.a.valid.token")
    assert "401" in str(exc_info.value.status_code)


# ============================================================
# Integration tests via HTTP client
# ============================================================


@pytest.mark.asyncio
async def test_register_success(client):
    """Register endpoint creates user and returns JWT."""
    resp = await client.post("/auth/register", json={
        "email": "newuser@test.com",
        "name": "Test User",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@test.com"
    assert data["name"] == "Test User"
    assert "token" in data
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Duplicate email returns 409."""
    await client.post("/auth/register", json={
        "email": "dup@test.com",
        "name": "User 1",
        "password": "password123",
    })
    resp = await client.post("/auth/register", json={
        "email": "dup@test.com",
        "name": "User 2",
        "password": "password456",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password(client):
    """Password under 8 chars returns 400."""
    resp = await client.post("/auth/register", json={
        "email": "short@test.com",
        "name": "Short Pw",
        "password": "abc",
    })
    assert resp.status_code == 400
    assert "8 characters" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client):
    """Login returns JWT for registered user."""
    await client.post("/auth/register", json={
        "email": "login@test.com",
        "name": "Login User",
        "password": "password123",
    })
    resp = await client.post("/auth/login", json={
        "email": "login@test.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "login@test.com"
    assert "token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Wrong password returns 401."""
    await client.post("/auth/register", json={
        "email": "wrongpw@test.com",
        "name": "Wrong PW",
        "password": "password123",
    })
    resp = await client.post("/auth/login", json={
        "email": "wrongpw@test.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    """Unknown email returns 401."""
    resp = await client.post("/auth/login", json={
        "email": "nobody@test.com",
        "password": "password123",
    })
    assert resp.status_code == 401
