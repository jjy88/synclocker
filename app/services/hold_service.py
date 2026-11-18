from app import config
from app.db import pool
from app.errors import Forbidden, NoLockerAvailable, NotFound
from app.ids import new_id
from app.repositories import holds as holds_repo
from app.repositories import idempotency as idem_repo
from app.repositories import lockers as lockers_repo
from app.repositories import sessions as sessions_repo


def _hold_body(row, status: str | None = None) -> dict:
    return {
        "hold_id": row["id"],
        "locker_id": row["locker_id"],
        "status": status or row["status"],
        "expires_at": row["expires_at"].isoformat(),
    }


def create_hold(user_id: str, session_id: str, size: str, idempotency_key: str) -> dict:
    """Reserve one locker of the requested size for a session, for HOLD_TTL_MINUTES.

    Everything runs in ONE database transaction:
      1. claim the idempotency key (a retry with the same key returns the stored response)
      2. lock the candidate locker rows (FOR UPDATE), so concurrent requests queue up here
      3. pick the first free locker and insert the hold
    If no locker is free, NoLockerAvailable is raised and the whole transaction rolls back,
    including the idempotency key.
    """
    with pool.connection() as conn:
        session = sessions_repo.get(conn, session_id)
        if session is None:
            raise NotFound("Session not found")

        if not idem_repo.claim(conn, user_id, idempotency_key):
            return idem_repo.get(conn, user_id, idempotency_key)

        locker_ids = lockers_repo.lock_candidates(conn, session["location_id"], size)
        for locker_id in locker_ids:
            if lockers_repo.is_free(conn, session_id, locker_id):
                row = holds_repo.insert(
                    conn, new_id("hld"), session_id, locker_id, user_id, config.HOLD_TTL_MINUTES
                )
                body = _hold_body(row)
                idem_repo.save_response(conn, user_id, idempotency_key, body)
                return body

        raise NoLockerAvailable()


def get_hold(user_id: str, hold_id: str) -> dict:
    with pool.connection() as conn:
        row = holds_repo.get(conn, hold_id)
    if row is None:
        raise NotFound("Hold not found")
    # Authorization is enforced here in the service layer: a user may only see their own holds.
    if row["user_id"] != user_id:
        raise Forbidden()
    status = "EXPIRED" if row["status"] == "HELD" and row["overdue"] else row["status"]
    return _hold_body(row, status)
