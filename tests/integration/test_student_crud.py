"""
Integration tests for app.crud.student against a real (test) database
session — one layer below the HTTP tests in test_student_api.py, verifying
CRUD behavior directly without going through routing/RBAC.
"""
import pytest
from fastapi import HTTPException

from app.crud import student as crud
from app.schemas.student import StudentCreate
from tests.utils.factories import unique_email, unique_phone

pytestmark = pytest.mark.integration


def _payload(**overrides) -> StudentCreate:
    return StudentCreate(
        name="Katherine Johnson",
        email=unique_email("crud"),
        phone=unique_phone(),
        course="B.Sc",
        semester=1,
        **overrides,
    )


def test_create_student_persists_and_returns_the_row(db_session):
    created = crud.create_student(db_session, _payload())
    assert created.id is not None

    fetched = crud.get_student_by_id(db_session, created.id)
    assert fetched.email == created.email


def test_create_student_raises_409_on_duplicate_email(db_session):
    payload = _payload()
    crud.create_student(db_session, payload)

    with pytest.raises(HTTPException) as exc_info:
        crud.create_student(db_session, payload)
    assert exc_info.value.status_code == 409


def test_delete_student_returns_none_when_missing(db_session):
    assert crud.delete_student(db_session, 999999) is None
