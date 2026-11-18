from psycopg.types.json import Jsonb


def claim(conn, user_id: str, key: str) -> bool:
    """Try to register the key. Returns True if this request is the first one to use it.

    If another transaction is inserting the same (user_id, key) right now, this statement
    waits until that transaction commits or rolls back.
    """
    cur = conn.execute(
        "INSERT INTO idempotency_keys (user_id, key) VALUES (%s, %s) ON CONFLICT (user_id, key) DO NOTHING",
        (user_id, key),
    )
    return cur.rowcount == 1


def get(conn, user_id: str, key: str) -> dict:
    row = conn.execute(
        "SELECT response_body FROM idempotency_keys WHERE user_id = %s AND key = %s",
        (user_id, key),
    ).fetchone()
    return row["response_body"]


def save_response(conn, user_id: str, key: str, body: dict) -> None:
    conn.execute(
        "UPDATE idempotency_keys SET response_body = %s WHERE user_id = %s AND key = %s",
        (Jsonb(body), user_id, key),
    )
