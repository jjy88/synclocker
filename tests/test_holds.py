import threading
import uuid

from app.errors import NoLockerAvailable
from app.services import hold_service
from tests.conftest import db_execute, hold, make_world


def test_hold_success_response_shape(client, user):
    w = make_world()
    r = hold(client, user, w["session_id"])
    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"hold_id", "locker_id", "status", "expires_at"}
    assert body["status"] == "HELD"


def test_second_user_gets_409_when_locker_taken(client, user, make_another_user):
    w = make_world(lockers=1)
    assert hold(client, user, w["session_id"]).status_code == 201
    r = hold(client, make_another_user(), w["session_id"])
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "NO_LOCKER_AVAILABLE"


def test_wrong_size_has_no_locker(client, user):
    w = make_world(lockers=1, size="large")
    assert hold(client, user, w["session_id"], size="small").status_code == 409


def test_missing_idempotency_key_is_400(client, user):
    w = make_world()
    r = client.post(f"/sessions/{w['session_id']}/holds", json={"size": "large"}, headers=user["headers"])
    assert r.status_code == 400


def test_invalid_size_is_400(client, user):
    w = make_world()
    r = client.post(
        f"/sessions/{w['session_id']}/holds",
        json={"size": "huge"},
        headers={**user["headers"], "Idempotency-Key": "k"},
    )
    assert r.status_code == 400
    assert "Traceback" not in r.text


def test_unknown_session_is_404(client, user):
    assert hold(client, user, "ses_does_not_exist").status_code == 404


def test_idempotent_retry_returns_same_hold_and_creates_one_row(client, user):
    w = make_world(lockers=3)
    key = str(uuid.uuid4())
    first = hold(client, user, w["session_id"], key=key)
    second = hold(client, user, w["session_id"], key=key)
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    rows = db_execute("SELECT count(*) FROM holds WHERE session_id = %s", (w["session_id"],)).fetchone()
    assert rows[0] == 1


def test_failed_hold_is_not_cached_so_retry_can_succeed(client, user, make_another_user):
    w = make_world(lockers=1)
    first_user = make_another_user()
    h = hold(client, first_user, w["session_id"]).json()
    key = str(uuid.uuid4())
    assert hold(client, user, w["session_id"], key=key).status_code == 409
    db_execute("UPDATE holds SET expires_at = now() - interval '1 minute' WHERE id = %s", (h["hold_id"],))
    assert hold(client, user, w["session_id"], key=key).status_code == 201


def test_expired_hold_frees_the_locker(client, user, make_another_user):
    w = make_world(lockers=1)
    first = make_another_user()
    h = hold(client, first, w["session_id"]).json()
    db_execute("UPDATE holds SET expires_at = now() - interval '1 minute' WHERE id = %s", (h["hold_id"],))
    avail = client.get(f"/sessions/{w['session_id']}/availability").json()
    assert avail["lockers"][0]["available"] is True
    assert client.get(f"/holds/{h['hold_id']}", headers=first["headers"]).json()["status"] == "EXPIRED"
    assert hold(client, user, w["session_id"]).status_code == 201


def test_availability_reflects_hold(client, user):
    w = make_world(lockers=1)
    assert client.get(f"/sessions/{w['session_id']}/availability").json()["lockers"][0]["available"] is True
    hold(client, user, w["session_id"])
    assert client.get(f"/sessions/{w['session_id']}/availability").json()["lockers"][0]["available"] is False


def test_list_sessions(client):
    w = make_world()
    r = client.get(f"/locations/{w['location_id']}/sessions")
    assert r.status_code == 200 and r.json()[0]["session_id"] == w["session_id"]
    assert client.get("/locations/nope/sessions").status_code == 404


def test_checkout_is_not_implemented_yet(client, user):
    assert client.post("/holds/hld_x/checkout", headers=user["headers"]).status_code == 501


def test_concurrent_holds_never_double_book(client, make_another_user):
    """20 threads call the service at the same time for 3 lockers: exactly 3 succeed."""
    lockers, n = 3, 20
    w = make_world(lockers=lockers)
    users = [make_another_user() for _ in range(n)]
    barrier = threading.Barrier(n)
    outcomes = []
    guard = threading.Lock()

    def worker(u):
        barrier.wait()
        try:
            hold_service.create_hold(u["user_id"], w["session_id"], "large", str(uuid.uuid4()))
            result = "ok"
        except NoLockerAvailable:
            result = "conflict"
        with guard:
            outcomes.append(result)

    threads = [threading.Thread(target=worker, args=(u,)) for u in users]
    [t.start() for t in threads]
    [t.join() for t in threads]

    assert outcomes.count("ok") == lockers
    assert outcomes.count("conflict") == n - lockers
    distinct = db_execute(
        "SELECT count(DISTINCT locker_id), count(*) FROM holds WHERE session_id = %s AND status = 'HELD'",
        (w["session_id"],),
    ).fetchone()
    assert distinct == (lockers, lockers)


def test_unexpected_error_never_leaks_stack_trace(client):
    r = client.get("/no/such/route")
    assert r.status_code == 404
    assert "Traceback" not in r.text
