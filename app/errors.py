class DomainError(Exception):
    """Raised by the service layer. The interface layer translates it into an HTTP response."""

    status_code = 400
    code = "BAD_REQUEST"
    default_message = "Bad request"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class BadRequest(DomainError):
    status_code = 400
    code = "BAD_REQUEST"


class Unauthorized(DomainError):
    status_code = 401
    code = "UNAUTHORIZED"
    default_message = "Invalid or missing credentials"


class Forbidden(DomainError):
    status_code = 403
    code = "FORBIDDEN"
    default_message = "You do not have access to this resource"


class NotFound(DomainError):
    status_code = 404
    code = "NOT_FOUND"
    default_message = "Resource not found"


class NoLockerAvailable(DomainError):
    status_code = 409
    code = "NO_LOCKER_AVAILABLE"
    default_message = "No suitable locker is available for this session"


class EmailTaken(DomainError):
    status_code = 409
    code = "EMAIL_TAKEN"
    default_message = "This email is already registered"


class NotImplementedYet(DomainError):
    status_code = 501
    code = "NOT_IMPLEMENTED"
    default_message = "This operation is not implemented yet"
