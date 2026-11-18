# A locker is free for a session when it has no live hold and no confirmed reservation.
# A hold is live while status = 'HELD' and it has not passed expires_at.
_FREE_EXPR = """
    NOT EXISTS (
        SELECT 1 FROM holds h
        WHERE h.session_id = %(sid)s AND h.locker_id = l.id
          AND h.status = 'HELD' AND h.expires_at > now()
    )
    AND NOT EXISTS (
        SELECT 1 FROM reservations r
        WHERE r.session_id = %(sid)s AND r.locker_id = l.id
          AND r.status = 'CONFIRMED'
    )
"""


def lock_candidates(conn, location_id: str, size: str) -> list[str]:
    """Pessimistic lock: lock every locker row of this size at the location.

    Rows are locked in id order, so two requests can never deadlock each other.
    A second request blocks here until the first one commits or rolls back.
    """
    rows = conn.execute(
        "SELECT id FROM lockers WHERE location_id = %s AND size = %s ORDER BY id FOR UPDATE",
        (location_id, size),
    ).fetchall()
    return [r["id"] for r in rows]


def is_free(conn, session_id: str, locker_id: str) -> bool:
    row = conn.execute(
        f"SELECT ({_FREE_EXPR}) AS free FROM lockers l WHERE l.id = %(lid)s",
        {"sid": session_id, "lid": locker_id},
    ).fetchone()
    return bool(row and row["free"])


def list_with_availability(conn, session_id: str, location_id: str):
    return conn.execute(
        f"SELECT l.id AS locker_id, l.size, ({_FREE_EXPR}) AS available "
        "FROM lockers l WHERE l.location_id = %(loc)s ORDER BY l.id",
        {"sid": session_id, "loc": location_id},
    ).fetchall()
