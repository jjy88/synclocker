def insert(conn, hold_id: str, session_id: str, locker_id: str, user_id: str, ttl_minutes: int):
    return conn.execute(
        "INSERT INTO holds (id, session_id, locker_id, user_id, status, expires_at) "
        "VALUES (%s, %s, %s, %s, 'HELD', now() + make_interval(mins => %s)) "
        "RETURNING id, locker_id, status, expires_at",
        (hold_id, session_id, locker_id, user_id, ttl_minutes),
    ).fetchone()


def get(conn, hold_id: str):
    return conn.execute(
        "SELECT id, session_id, locker_id, user_id, status, expires_at, (expires_at <= now()) AS overdue "
        "FROM holds WHERE id = %s",
        (hold_id,),
    ).fetchone()
