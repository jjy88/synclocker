from app.db import pool
from app.errors import NotFound
from app.repositories import lockers as lockers_repo
from app.repositories import sessions as sessions_repo


def _session_view(row) -> dict:
    return {
        "session_id": row["id"],
        "location_id": row["location_id"],
        "name": row["name"],
        "starts_at": row["starts_at"],
        "ends_at": row["ends_at"],
        "price_cents": row["price_cents"],
    }


def list_sessions(location_id: str) -> list[dict]:
    with pool.connection() as conn:
        if not sessions_repo.location_exists(conn, location_id):
            raise NotFound("Location not found")
        return [_session_view(r) for r in sessions_repo.list_by_location(conn, location_id)]


def get_availability(session_id: str) -> dict:
    with pool.connection() as conn:
        session = sessions_repo.get(conn, session_id)
        if session is None:
            raise NotFound("Session not found")
        rows = lockers_repo.list_with_availability(conn, session_id, session["location_id"])
    return {"session_id": session_id, "lockers": rows}
