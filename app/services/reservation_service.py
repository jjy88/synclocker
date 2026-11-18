from app.db import pool
from app.errors import Forbidden, NotFound
from app.repositories import reservations as reservations_repo


def list_my_reservations(user_id: str) -> list[dict]:
    with pool.connection() as conn:
        rows = reservations_repo.list_for_user(conn, user_id)
    return [
        {
            "reservation_id": r["id"],
            "session_id": r["session_id"],
            "locker_id": r["locker_id"],
            "status": r["status"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def cancel_reservation(user_id: str, reservation_id: str) -> None:
    with pool.connection() as conn:
        row = reservations_repo.get(conn, reservation_id)
        if row is None:
            raise NotFound("Reservation not found")
        # Authorization is enforced here in the service layer.
        if row["user_id"] != user_id:
            raise Forbidden()
        reservations_repo.cancel(conn, reservation_id)
