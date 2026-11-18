from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.errors import Unauthorized
from app.services import auth_service

# auto_error=False so a missing header becomes our own 401 with our own error shape.
_bearer = HTTPBearer(auto_error=False)


def current_user_id(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    if creds is None:
        raise Unauthorized("Missing bearer token")
    return auth_service.decode_token(creds.credentials)
