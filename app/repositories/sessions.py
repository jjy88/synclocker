def location_exists(conn, location_id: str) -> bool:
    return conn.execute("SELECT 1 FROM locations WHERE id = %s", (location_id,)).fetchone() is not None


def list_by_location(conn, location_id: str):
    return conn.execute(
        "SELECT id, location_id, name, starts_at, ends_at, price_cents "
        "FROM rental_sessions WHERE location_id = %s ORDER BY starts_at",
        (location_id,),
    ).fetchall()


def get(conn, session_id: str):
    return conn.execute(
        "SELECT id, location_id, name, starts_at, ends_at, price_cents "
        "FROM rental_sessions WHERE id = %s",
        (session_id,),
    ).fetchone()
