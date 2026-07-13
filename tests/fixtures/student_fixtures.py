"""
Reusable fixtures for Student domain data. Loaded into the test session via
`pytest_plugins` in tests/conftest.py.
"""
import pytest

from app.models.student import Student
from tests.utils.factories import unique_email, unique_phone


@pytest.fixture()
def sample_student(db_session) -> Student:
    student = Student(
        name="Ada Lovelace",
        email=unique_email("student"),
        phone=unique_phone(),
        course="B.Tech",
        semester=1,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student
