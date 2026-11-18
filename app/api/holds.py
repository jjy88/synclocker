from fastapi import APIRouter, Depends, Header, Path

from app.api.common import errors
from app.api.deps import current_user_id
from app.errors import NotImplementedYet
from app.schemas import HoldRequest, HoldResponse
from app.services import hold_service

router = APIRouter(tags=["holds"])


@router.post(
    "/sessions/{session_id}/holds",
    status_code=201,
    response_model=HoldResponse,
    responses=errors(400, 401, 404, 409),
)
def create_hold(
    body: HoldRequest,
    session_id: str = Path(max_length=100),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=255),
    user_id: str = Depends(current_user_id),
):
    return hold_service.create_hold(user_id, session_id, body.size, idempotency_key)


@router.get("/holds/{hold_id}", response_model=HoldResponse, responses=errors(400, 401, 403, 404))
def get_hold(hold_id: str = Path(max_length=100), user_id: str = Depends(current_user_id)):
    return hold_service.get_hold(user_id, hold_id)


@router.post("/holds/{hold_id}/checkout", responses=errors(400, 401, 501))
def checkout(hold_id: str = Path(max_length=100), user_id: str = Depends(current_user_id)):
    # Planned for the Stripe integration milestone (async payment worker).
    raise NotImplementedYet("Checkout is not implemented yet")
