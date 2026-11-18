import uuid

import psycopg
import pytest
from fastapi.testclient import TestClient

from app import config, migrate
from app.main import app


@pytest.fixture(scope="session")
def client():
    migrate.run()
    with TestClient(app) as c:  # runs the lifespan, which opens the connection pool
        yield c


def db_execute(sql: str, params=()):
    with psycopg.connect(config.DATABASE_URL, autocommit=True) as conn:
        return conn.execute(sql, params)


def make_world(lockers: int = 1, size: str = "large") -> dict:
    """A fresh location, session and lockers, so tests never interfere with each other."""
    tag = uuid.uuid4().hex[:8]
    loc, ses = f"loc_t_{tag}", f"ses_t_{tag}"
    with psycopg.connect(config.DATABASE_URL, autocommit=True) as conn:
        conn.execute("INSERT INTO locations (id, name) VALUES (%s, 'Test')", (loc,))
        conn.execute(
            "INSERT INTO rental_sessions (id, location_id, name, starts_at, ends_at, price_cents) "
            "VALUES (%s, %s, 'Test session', now() + interval '1 day', now() + interval '2 days', 1000)",
            (ses, loc),
        )
        for i in range(lockers):
            conn.execute(
                "INSERT INTO lockers (id, location_id, size) VALUES (%s, %s, %s)",
                (f"lkr_t_{tag}_{i}", loc, size),
            )
    return {"location_id": loc, "session_id": ses}


@pytest.fixture
def world():
    return make_world


def make_user(client) -> dict:
    email = f"t_{uuid.uuid4().hex[:10]}@example.com"
    r = client.post("/auth/register", json={"email": email, "password": "password123"})
    assert r.status_code == 201, r.text
    user_id = r.json()["user_id"]
    r = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"user_id": user_id, "email": email, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def user(client):
    return make_user(client)


@pytest.fixture
def make_another_user(client):
    return lambda: make_user(client)


def hold(client, user, session_id, size="large", key=None):
    return client.post(
        f"/sessions/{session_id}/holds",
        json={"size": size},
        headers={**user["headers"], "Idempotency-Key": key or str(uuid.uuid4())},
    )
