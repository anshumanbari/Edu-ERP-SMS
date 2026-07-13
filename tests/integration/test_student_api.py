"""
Integration tests for /students — full HTTP round-trip through the real
FastAPI app against a real (test) database, including RBAC enforcement.
"""
import pytest

from tests.utils.factories import unique_email, unique_phone

pytestmark = pytest.mark.integration

VALID_PAYLOAD = {
    "name": "Grace Hopper",
    "course": "B.Tech",
    "semester": 2,
}


def _student_payload(**overrides):
    return {
        **VALID_PAYLOAD,
        "email": unique_email("student-api"),
        "phone": unique_phone(),
        **overrides,
    }


def test_create_student_requires_authentication(client):
    response = client.post("/students/", json=_student_payload())
    assert response.status_code == 401


def test_create_student_denies_student_role(client, student_headers):
    response = client.post("/students/", json=_student_payload(), headers=student_headers)
    assert response.status_code == 403


def test_create_student_allows_admin(client, admin_headers):
    response = client.post("/students/", json=_student_payload(), headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["data"]["course"] == "B.Tech"


def test_create_student_allows_teacher(client, teacher_headers):
    response = client.post("/students/", json=_student_payload(), headers=teacher_headers)
    assert response.status_code == 201


def test_create_student_duplicate_email_returns_409(client, admin_headers):
    payload = _student_payload()
    first = client.post("/students/", json=payload, headers=admin_headers)
    assert first.status_code == 201

    second = client.post("/students/", json={**payload, "name": "Duplicate"}, headers=admin_headers)
    assert second.status_code == 409


def test_get_student_by_id_returns_404_when_missing(client):
    response = client.get("/students/999999")
    assert response.status_code == 404


def test_get_student_by_id_returns_the_record(client, sample_student):
    response = client.get(f"/students/{sample_student.id}")
    assert response.status_code == 200
    assert response.json()["data"]["email"] == sample_student.email


def test_list_students_includes_created_record(client, sample_student):
    response = client.get("/students/")
    assert response.status_code == 200
    body = response.json()["data"]
    emails = [s["email"] for s in body["students"]]
    assert sample_student.email in emails


def test_update_student_denies_student_role(client, student_headers, sample_student):
    response = client.put(
        f"/students/{sample_student.id}",
        json=_student_payload(email=sample_student.email),
        headers=student_headers,
    )
    assert response.status_code == 403


def test_update_student_allows_admin(client, admin_headers, sample_student):
    response = client.put(
        f"/students/{sample_student.id}",
        json=_student_payload(email=sample_student.email, semester=5),
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["semester"] == 5


def test_delete_student_denies_teacher_role(client, teacher_headers, sample_student):
    response = client.delete(f"/students/{sample_student.id}", headers=teacher_headers)
    assert response.status_code == 403


def test_delete_student_allows_admin(client, admin_headers, sample_student):
    response = client.delete(f"/students/{sample_student.id}", headers=admin_headers)
    assert response.status_code == 200

    follow_up = client.get(f"/students/{sample_student.id}")
    assert follow_up.status_code == 404
