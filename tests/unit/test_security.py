"""
Unit tests for app.core.security — password hashing and JWT lifecycle.
No database, no HTTP, no fixtures beyond plain function calls.
"""
import pytest
from fastapi import HTTPException

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

pytestmark = pytest.mark.unit


def test_hash_password_does_not_store_plaintext():
    hashed = hash_password("CorrectHorseBattery1")
    assert hashed != "CorrectHorseBattery1"


def test_verify_password_accepts_correct_password():
    hashed = hash_password("CorrectHorseBattery1")
    assert verify_password("CorrectHorseBattery1", hashed) is True


def test_verify_password_rejects_incorrect_password():
    hashed = hash_password("CorrectHorseBattery1")
    assert verify_password("WrongPassword1", hashed) is False


def test_access_token_round_trip():
    token = create_access_token(subject="user@example.com")
    assert decode_access_token(token) == "user@example.com"


def test_decode_access_token_rejects_garbage_token():
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not-a-real-token")
    assert exc_info.value.status_code == 401
