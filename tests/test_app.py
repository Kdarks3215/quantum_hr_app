import json

import pytest

from app import create_app, db
from app.models import User


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
            "JWT_SECRET_KEY": "test-jwt-secret",
            "SEED_DEFAULT_DATA": False,
        }
    )

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_token(app, client):
    payload = {"username": "tester", "password": "password123", "role": "admin"}
    response = client.post("/api/auth/register", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 201

    response = client.post(
        "/api/auth/login",
        data=json.dumps({"username": "tester", "password": "password123"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    return response.get_json()["access_token"]


def test_user_registration_and_login(client):
    payload = {"username": "alice", "password": "securepass"}
    response = client.post("/api/auth/register", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 201

    response = client.post("/api/auth/login", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert data["user"]["username"] == "alice"


def test_unauthorized_access_blocked(client):
    payload = {
        "user_id": 1,
        "name": "John Doe",
        "role": "Stylist",
        "salary": 5000,
        "start_date": "2024-01-01",
        "leave_days": 10,
    }
    response = client.post("/api/employees", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 401


def test_crud_operations_with_auth(app, client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # create supporting user via API
    response = client.post(
        "/api/auth/register",
        data=json.dumps({"username": "jane.employee", "password": "pass123", "role": "user"}),
        content_type="application/json",
    )
    assert response.status_code == 201

    with app.app_context():
        employee_user_id = User.query.filter_by(username="jane.employee").first().id

    create_payload = {
        "user_id": employee_user_id,
        "name": "Jane Doe",
        "role": "Manager",
        "salary": 6500,
        "start_date": "2024-01-01",
        "leave_days": 15,
    }
    create_resp = client.post("/api/employees", data=json.dumps(create_payload), headers=headers)
    assert create_resp.status_code == 201
    employee = create_resp.get_json()
    employee_id = employee["id"]
    assert employee["salary_currency"] == "GHS"

    list_resp = client.get("/api/employees", headers=headers)
    assert list_resp.status_code == 200
    assert any(item["id"] == employee_id for item in list_resp.get_json())

    update_resp = client.put(
        f"/api/employees/{employee_id}",
        data=json.dumps({"role": "Senior Manager", "salary": 7000, "leave_days": 20}),
        headers=headers,
    )
    assert update_resp.status_code == 200
    updated = update_resp.get_json()
    assert updated["role"] == "Senior Manager"
    assert updated["salary"] == 7000
    assert updated["leave_days"] == 20

    delete_resp = client.delete(f"/api/employees/{employee_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.get_json()["message"] == "Employee deleted."

    list_resp = client.get("/api/employees", headers=headers)
    assert all(item["id"] != employee_id for item in list_resp.get_json())
