def list_for_user(conn, user_id: str):
    return conn.execute(
        "SELECT id, session_id, locker_id, status, created_at "
        "FROM reservations WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()


def get(conn, reservation_id: str):
    return conn.execute(
        "SELECT id, session_id, locker_id, user_id, status FROM reservations WHERE id = %s",
        (reservation_id,),
    ).fetchone()


def cancel(conn, reservation_id: str) -> None:
    conn.execute(
        "UPDATE reservations SET status = 'CANCELLED' WHERE id = %s AND status = 'CONFIRMED'",
        (reservation_id,),
    )
