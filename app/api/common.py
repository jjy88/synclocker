from app.schemas import ErrorResponse

_DESCRIPTIONS = {
    400: "Invalid input",
    401: "Missing, invalid, or expired token",
    403: "The resource belongs to another user",
    404: "Resource not found",
    409: "Conflict",
    501: "Not implemented yet",
}


def errors(*codes: int) -> dict:
    """OpenAPI documentation of error responses. Every error uses the ErrorResponse shape."""
    return {c: {"model": ErrorResponse, "description": _DESCRIPTIONS[c]} for c in codes}
