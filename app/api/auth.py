from fastapi import APIRouter

from app.api.common import errors
from app.schemas import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=RegisterResponse, responses=errors(400, 409))
def register(body: RegisterRequest):
    return auth_service.register(body.email, body.password)


@router.post("/login", response_model=TokenResponse, responses=errors(400, 401))
def login(body: LoginRequest):
    return auth_service.login(body.email, body.password)
