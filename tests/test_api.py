import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def make_user(email="a@test.com", pw="secret123"):
    client.post("/auth/register", json={"email": email, "password": pw})
    r = client.post("/auth/login", data={"username": email, "password": pw})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def test_register_duplicate_email():
    client.post("/auth/register", json={"email": "a@test.com", "password": "secret123"})
    r = client.post("/auth/register", json={"email": "a@test.com", "password": "secret123"})
    assert r.status_code == 409


def test_login_wrong_password():
    make_user()
    r = client.post("/auth/login", data={"username": "a@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_tasks_need_token():
    assert client.get("/tasks").status_code == 401


def test_task_crud():
    h = make_user()
    r = client.post("/tasks", json={"title": "Learn FastAPI"}, headers=h)
    assert r.status_code == 201
    tid = r.json()["id"]
    r = client.patch(f"/tasks/{tid}", json={"done": True}, headers=h)
    assert r.json()["done"] is True
    assert len(client.get("/tasks?done=true", headers=h).json()) == 1
    assert client.delete(f"/tasks/{tid}", headers=h).status_code == 204
    assert client.get("/tasks", headers=h).json() == []


def test_user_cannot_touch_others_task():
    h1 = make_user("a@test.com")
    h2 = make_user("b@test.com")
    tid = client.post("/tasks", json={"title": "private"}, headers=h1).json()["id"]
    assert client.patch(f"/tasks/{tid}", json={"done": True}, headers=h2).status_code == 404
    assert client.get("/tasks", headers=h2).json() == []


def test_health_check():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
