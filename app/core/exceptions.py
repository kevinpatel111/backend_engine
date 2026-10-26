"""Custom application domain exceptions."""

from typing import Any


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 400, details: Any | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: Any | None = None) -> None:
        super().__init__(message=message, status_code=404, details=details)


class ConflictException(AppException):
    def __init__(
        self, message: str = "Resource conflict occurred", details: Any | None = None
    ) -> None:
        super().__init__(message=message, status_code=409, details=details)


class UnauthorizedException(AppException):
    def __init__(
        self, message: str = "Could not validate credentials", details: Any | None = None
    ) -> None:
        super().__init__(message=message, status_code=401, details=details)


class ForbiddenException(AppException):
    def __init__(
        self,
        message: str = "You do not have permission to access this resource",
        details: Any | None = None,
    ) -> None:
        super().__init__(message=message, status_code=403, details=details)


class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request", details: Any | None = None) -> None:
        super().__init__(message=message, status_code=400, details=details)
