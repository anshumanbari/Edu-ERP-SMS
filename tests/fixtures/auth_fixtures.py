"""
Reusable fixtures for authenticated test users, one per role. Loaded into
the test session via `pytest_plugins` in tests/conftest.py.

Users are inserted directly via the ORM rather than through
`crud.create_user`/`UserCreate`, because `UserCreate.role` is intentionally
restricted to student/teacher at the schema level (self-registration can't
create an admin — see app/schemas/user.py and docs/05_SECURITY_ARCHITECTURE.md
§3). Test fixtures need to produce an admin user directly, the same way a
real deployment's first admin would be provisioned out-of-band.
"""
import pytest

from app.core.roles import Role
from app.core.security import create_access_token, hash_password
from app.models.user import User
from tests.utils.factories import unique_email


def _make_user(db_session, role: Role) -> User:
    user = User(
        name=f"Test {role.value.title()}",
        email=unique_email(role.value),
        hashed_password=hash_password("TestPassword123"),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(user: User) -> dict:
    token = create_access_token(subject=user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_user(db_session) -> User:
    return _make_user(db_session, Role.ADMIN)


@pytest.fixture()
def teacher_user(db_session) -> User:
    return _make_user(db_session, Role.TEACHER)


@pytest.fixture()
def student_user(db_session) -> User:
    return _make_user(db_session, Role.STUDENT)


@pytest.fixture()
def admin_headers(admin_user) -> dict:
    return _auth_headers(admin_user)


@pytest.fixture()
def teacher_headers(teacher_user) -> dict:
    return _auth_headers(teacher_user)


@pytest.fixture()
def student_headers(student_user) -> dict:
    return _auth_headers(student_user)
