from fastapi import APIRouter, Path

from app.api.common import errors
from app.schemas import AvailabilityResponse, SessionOut
from app.services import availability_service

router = APIRouter(tags=["sessions"])


@router.get(
    "/locations/{location_id}/sessions",
    response_model=list[SessionOut],
    responses=errors(400, 404),
)
def list_sessions(location_id: str = Path(max_length=100)):
    return availability_service.list_sessions(location_id)


@router.get(
    "/sessions/{session_id}/availability",
    response_model=AvailabilityResponse,
    responses=errors(400, 404),
)
def get_availability(session_id: str = Path(max_length=100)):
    return availability_service.get_availability(session_id)
