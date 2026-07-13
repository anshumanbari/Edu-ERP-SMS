"""
Integration tests for /auth — exercises the real FastAPI app, real routing,
real RBAC/JWT wiring, and a real (test) Postgres database via the `client`
fixture (see tests/conftest.py).
"""
import pytest

from tests.utils.factories import unique_email

pytestmark = pytest.mark.integration


def test_register_student_succeeds(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "New Student",
            "email": unique_email("register"),
            "password": "StrongPass1",
            "role": "student",
        },
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["role"] == "student"
    assert "hashed_password" not in body


def test_register_admin_is_rejected_at_the_schema_level(client):
    """
    UserCreate.role only accepts student/teacher — self-registration can
    never create an admin (docs/05_SECURITY_ARCHITECTURE.md §3).
    """
    response = client.post(
        "/auth/register",
        json={
            "name": "Sneaky Admin",
            "email": unique_email("sneaky"),
            "password": "StrongPass1",
            "role": "admin",
        },
    )
    assert response.status_code == 422


def test_register_duplicate_email_returns_409(client):
    email = unique_email("dup")
    payload = {"name": "First", "email": email, "password": "StrongPass1", "role": "student"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json={**payload, "name": "Second"})
    assert second.status_code == 409


def test_login_with_correct_credentials_returns_token(client):
    email = unique_email("login")
    client.post(
        "/auth/register",
        json={"name": "Login User", "email": email, "password": "StrongPass1", "role": "student"},
    )

    response = client.post("/auth/login", data={"username": email, "password": "StrongPass1"})
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_wrong_password_returns_401(client):
    email = unique_email("badlogin")
    client.post(
        "/auth/register",
        json={"name": "Bad Login User", "email": email, "password": "StrongPass1", "role": "student"},
    )

    response = client.post("/auth/login", data={"username": email, "password": "WrongPassword1"})
    assert response.status_code == 401


def test_me_requires_a_valid_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_the_authenticated_user(client, student_headers, student_user):
    response = client.get("/auth/me", headers=student_headers)
    assert response.status_code == 200
    assert response.json()["data"]["email"] == student_user.email
