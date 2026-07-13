"""
Unit tests for app.schemas.student — Pydantic validation only, no database,
no HTTP. Exercises the schema layer in isolation from CRUD/routers.
"""
import pytest
from pydantic import ValidationError

from app.schemas.student import StudentCreate

pytestmark = pytest.mark.unit


VALID_PAYLOAD = {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "phone": 9876543210,
    "course": "B.Tech",
    "semester": 3,
}


def test_valid_payload_is_accepted():
    student = StudentCreate(**VALID_PAYLOAD)
    assert student.name == "Ada Lovelace"
    assert student.semester == 3


def test_phone_below_minimum_digits_is_rejected():
    payload = {**VALID_PAYLOAD, "phone": 123}
    with pytest.raises(ValidationError):
        StudentCreate(**payload)


def test_semester_out_of_range_is_rejected():
    payload = {**VALID_PAYLOAD, "semester": 9}
    with pytest.raises(ValidationError):
        StudentCreate(**payload)


def test_unknown_field_is_rejected():
    payload = {**VALID_PAYLOAD, "gpa": 4.0}
    with pytest.raises(ValidationError):
        StudentCreate(**payload)


def test_invalid_email_is_rejected():
    payload = {**VALID_PAYLOAD, "email": "not-an-email"}
    with pytest.raises(ValidationError):
        StudentCreate(**payload)
