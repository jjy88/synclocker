from fastapi import APIRouter, Depends, Path

from app.api.common import errors
from app.api.deps import current_user_id
from app.schemas import ReservationOut
from app.services import reservation_service

router = APIRouter(tags=["reservations"])


@router.get("/me/reservations", response_model=list[ReservationOut], responses=errors(400, 401))
def list_my_reservations(user_id: str = Depends(current_user_id)):
    return reservation_service.list_my_reservations(user_id)


@router.delete(
    "/reservations/{reservation_id}",
    status_code=204,
    responses=errors(400, 401, 403, 404),
)
def cancel_reservation(
    reservation_id: str = Path(max_length=100), user_id: str = Depends(current_user_id)
):
    reservation_service.cancel_reservation(user_id, reservation_id)
