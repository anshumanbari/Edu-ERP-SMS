class AppException(Exception):
    """
    Base class for all custom application exceptions.

    Any subclass raised in a router/crud function is caught by the global
    handler registered in app.core.error_handlers and converted into the
    standard JSON error response.
    """

    def __init__(self, message: str, status_code: int = 400, error_code: str | None = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found."):
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict occurred."):
        super().__init__(message, status_code=409, error_code="CONFLICT")


class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request."):
        super().__init__(message, status_code=400, error_code="BAD_REQUEST")


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized."):
        super().__init__(message, status_code=401, error_code="UNAUTHORIZED")


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden."):
        super().__init__(message, status_code=403, error_code="FORBIDDEN")
