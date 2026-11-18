"""Data-source layer: SQL only, no business rules."""


def insert(conn, user_id: str, email: str, password_hash: str) -> None:
    conn.execute(
        "INSERT INTO users (id, email, password_hash) VALUES (%s, %s, %s)",
        (user_id, email, password_hash),
    )


def get_by_email(conn, email: str):
    return conn.execute(
        "SELECT id, email, password_hash FROM users WHERE email = %s", (email,)
    ).fetchone()
