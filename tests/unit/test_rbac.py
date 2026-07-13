"""
Unit tests for app.core.rbac.require_roles — role-check logic exercised
directly as a plain function call, bypassing FastAPI's dependency-injection
machinery entirely, so no app, no database, no HTTP is involved.
"""
from types import SimpleNamespace

import pytest

from app.core.exceptions import ForbiddenException
from app.core.rbac import require_roles
from app.core.roles import Role

pytestmark = pytest.mark.unit


def _fake_user(role: Role) -> SimpleNamespace:
    return SimpleNamespace(role=role)


def test_allowed_role_passes_through():
    check = require_roles(Role.ADMIN, Role.TEACHER)
    user = _fake_user(Role.TEACHER)
    assert check(current_user=user) is user


def test_disallowed_role_raises_forbidden():
    check = require_roles(Role.ADMIN)
    user = _fake_user(Role.STUDENT)
    with pytest.raises(ForbiddenException):
        check(current_user=user)
