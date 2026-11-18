import base64
import json
from datetime import datetime, timedelta, timezone

import jwt

from app import config
from tests.conftest import hold, make_world


def _forge(payload: dict, key, algorithm: str) -> str:
    return jwt.encode(payload, key, algorithm=algorithm)


def _claims(sub: str, **extra) -> dict:
    return {"sub": sub, "exp": datetime.now(timezone.utc) + timedelta(hours=1), **extra}


def test_register_duplicate_email_conflicts(client, user):
    r = client.post("/auth/register", json={"email": user["email"], "password": "password123"})
    assert r.status_code == 409


def test_register_rejects_bad_input(client):
    assert client.post("/auth/register", json={"email": "not-an-email", "password": "password123"}).status_code == 400
    assert client.post("/auth/register", json={"email": "a@b.co", "password": "short"}).status_code == 400


def test_login_wrong_password_is_401(client, user):
    r = client.post("/auth/login", json={"email": user["email"], "password": "wrong-password"})
    assert r.status_code == 401


def test_protected_route_without_token_is_401(client):
    assert client.get("/me/reservations").status_code == 401


def test_garbage_token_is_401(client):
    r = client.get("/me/reservations", headers={"Authorization": "Bearer not.a.token"})
    assert r.status_code == 401


def test_token_signed_with_wrong_secret_is_401(client, user):
    forged = _forge(_claims(user["user_id"]), "attacker-secret-attacker-secret-1234", "HS256")
    r = client.get("/me/reservations", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


def test_tampered_payload_is_401(client, user):
    header, payload, signature = user["token"].split(".")
    data = json.loads(base64.urlsafe_b64decode(payload + "=="))
    data["sub"] = "usr_someone_else"
    new_payload = base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()
    tampered = f"{header}.{new_payload}.{signature}"
    r = client.get("/me/reservations", headers={"Authorization": f"Bearer {tampered}"})
    assert r.status_code == 401


def test_alg_none_token_is_401(client, user):
    forged = _forge(_claims(user["user_id"]), None, "none")
    r = client.get("/me/reservations", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


def test_expired_token_is_401(client, user):
    expired = _forge(
        {"sub": user["user_id"], "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        config.JWT_SECRET,
        "HS256",
    )
    r = client.get("/me/reservations", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_create_hold_without_token_is_401(client):
    w = make_world()
    r = client.post(
        f"/sessions/{w['session_id']}/holds", json={"size": "large"}, headers={"Idempotency-Key": "k1"}
    )
    assert r.status_code == 401


def test_user_cannot_read_another_users_hold(client, user, make_another_user):
    w = make_world()
    h = hold(client, user, w["session_id"]).json()
    other = make_another_user()
    assert client.get(f"/holds/{h['hold_id']}", headers=other["headers"]).status_code == 403
    assert client.get(f"/holds/{h['hold_id']}", headers=user["headers"]).status_code == 200


def test_user_cannot_cancel_another_users_reservation(client, user, make_another_user):
    from tests.conftest import db_execute

    w = make_world()
    h = hold(client, user, w["session_id"]).json()
    reservation_id = "res_test_" + h["hold_id"][-6:]
    db_execute(
        "INSERT INTO reservations (id, session_id, locker_id, hold_id, user_id, status) "
        "VALUES (%s, %s, %s, %s, %s, 'CONFIRMED')",
        (reservation_id, w["session_id"], h["locker_id"], h["hold_id"], user["user_id"]),
    )
    other = make_another_user()
    assert client.delete(f"/reservations/{reservation_id}", headers=other["headers"]).status_code == 403
    assert client.get("/me/reservations", headers=other["headers"]).json() == []
    mine = client.get("/me/reservations", headers=user["headers"]).json()
    assert [r["reservation_id"] for r in mine] == [reservation_id]
    assert client.delete(f"/reservations/{reservation_id}", headers=user["headers"]).status_code == 204
    status = client.get("/me/reservations", headers=user["headers"]).json()[0]["status"]
    assert status == "CANCELLED"
