"""
Small, dependency-free helpers for generating unique test data. Kept
separate from fixtures/ — these are plain functions any test or fixture
can call directly, not pytest fixtures themselves.
"""
import random
import uuid


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}.{uuid.uuid4().hex[:12]}@example.com"


def unique_phone() -> int:
    return random.randint(6_000_000_000, 9_999_999_999)
