from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class CommercePulseError(Exception):
    """Base exception class for all CommercePulse domain errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.error_code = error_code or self.__class__.error_code
        self.status_code = status_code or self.__class__.status_code
        self.details = details
        super().__init__(self.message)


class AuthenticationError(CommercePulseError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_FAILED"
    message = "Could not validate credentials."


class InvalidTokenError(AuthenticationError):
    error_code = "INVALID_TOKEN"
    message = "The provided token is invalid or expired."


class ExpiredTokenError(AuthenticationError):
    error_code = "EXPIRED_TOKEN"
    message = "The provided token has expired."


class MissingTokenError(AuthenticationError):
    error_code = "MISSING_TOKEN"
    message = "No authentication token was provided."


class AuthorizationError(CommercePulseError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "INSUFFICIENT_PERMISSIONS"
    message = "You do not have permission to perform this action."


class RoleRequiredError(AuthorizationError):
    error_code = "ROLE_REQUIRED"

    def __init__(self, required_roles: list[str], **kwargs: Any) -> None:
        super().__init__(
            message=f"Requires one of the following roles: {', '.join(required_roles)}",
            details={"required_roles": required_roles},
            **kwargs,
        )


class PermissionRequiredError(AuthorizationError):
    error_code = "PERMISSION_REQUIRED"

    def __init__(self, required_permissions: list[str], **kwargs: Any) -> None:
        super().__init__(
            message=f"Requires the following permissions: {', '.join(required_permissions)}",
            details={"required_permissions": required_permissions},
            **kwargs,
        )


class InactiveUserError(CommercePulseError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "INACTIVE_USER"
    message = "This user account has been deactivated."


class NotFoundError(CommercePulseError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"
    message = "The requested resource was not found."


class ConflictError(CommercePulseError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"
    message = "A resource with this identifier already exists."


class ValidationError(CommercePulseError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "VALIDATION_ERROR"
    message = "The provided data was invalid."


class RateLimitExceededError(CommercePulseError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please slow down."


class ServiceUnavailableError(CommercePulseError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"
    message = "Service is temporarily unavailable. Please try again later."


class ExternalServiceError(CommercePulseError):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "EXTERNAL_SERVICE_ERROR"
    message = "An external service failed to respond correctly."


class StripeError(CommercePulseError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "STRIPE_ERROR"
    message = "Payment processing failed."


class DatabaseError(CommercePulseError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "DATABASE_ERROR"
    message = "A database operation failed."


class TenantIsolationError(AuthorizationError):
    error_code = "TENANT_ISOLATION_VIOLATION"
    message = "Attempted to access resources outside organization scope."


class PasswordValidationError(ValidationError):
    error_code = "PASSWORD_VALIDATION_ERROR"
    message = "Password validation failed."


class CSRFValidationError(ValidationError):
    status_code = 403
    error_code = "CSRF_VALIDATION_ERROR"
    message = "CSRF token validation failed."


class BadRequestError(CommercePulseError):
    status_code = 400
    error_code = "BAD_REQUEST"
    message = "The request could not be understood or was missing required parameters."


@dataclass(slots=True)
class ErrorResponse:
    error: str
    message: str
    status_code: int
    request_id: str
    details: dict[str, Any] | list[Any] | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "error": self.error,
            "message": self.message,
            "status_code": self.status_code,
            "request_id": self.request_id,
        }
        if self.details is not None:
            result["details"] = self.details
        return {"error": result}


def format_error_response(
    *,
    error_code: str,
    message: str,
    status_code: int,
    request_id: str,
    details: dict[str, Any] | list[Any] | None = None,
) -> dict[str, Any]:
    return ErrorResponse(
        error=error_code,
        message=message,
        status_code=status_code,
        request_id=request_id,
        details=details,
    ).to_dict()


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid.uuid4()))


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


T = TypeVar("T", bound=FastAPI)


class ErrorHandlerRegistry(Generic[T]):
    @staticmethod
    def register(app: T) -> None:
        @app.exception_handler(CommercePulseError)
        async def handle_commercepulse_error(request: Request, exc: CommercePulseError) -> JSONResponse:
            request_id = get_request_id(request)
            return JSONResponse(
                status_code=exc.status_code,
                content=jsonable_encoder(
                    format_error_response(
                        error_code=exc.error_code,
                        message=exc.message,
                        status_code=exc.status_code,
                        request_id=request_id,
                        details=exc.details,
                    )
                ),
            )

        @app.exception_handler(StarletteHTTPException)
        async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
            request_id = get_request_id(request)
            error_map: dict[int, str] = {
                status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
                status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
                status.HTTP_403_FORBIDDEN: "FORBIDDEN",
                status.HTTP_404_NOT_FOUND: "NOT_FOUND",
                status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
                status.HTTP_422_UNPROCESSABLE_ENTITY: "UNPROCESSABLE_ENTITY",
                status.HTTP_429_TOO_MANY_REQUESTS: "TOO_MANY_REQUESTS",
                status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
            }
            error_code = error_map.get(exc.status_code, "HTTP_ERROR")
            return JSONResponse(
                status_code=exc.status_code,
                content=jsonable_encoder(
                    format_error_response(
                        error_code=error_code,
                        message=str(exc.detail) if isinstance(exc.detail, str) else "Request failed.",
                        status_code=exc.status_code,
                        request_id=request_id,
                        details=exc.detail if not isinstance(exc.detail, str) else None,
                    )
                ),
            )

        @app.exception_handler(RequestValidationError)
        async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
            request_id = get_request_id(request)
            formatted_errors = []
            for err in exc.errors():
                loc = " -> ".join(str(loc) for loc in err.get("loc", []))
                formatted_errors.append(
                    {
                        "loc": err.get("loc"),
                        "field": loc,
                        "message": err.get("msg", ""),
                        "type": err.get("type"),
                        "input": err.get("input"),
                    }
                )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=jsonable_encoder(
                    format_error_response(
                        error_code="VALIDATION_ERROR",
                        message="Request validation failed. Please check the provided data.",
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        request_id=request_id,
                        details=formatted_errors,
                    )
                ),
            )

        @app.exception_handler(Exception)
        async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
            request_id = get_request_id(request)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=jsonable_encoder(
                    format_error_response(
                        error_code="INTERNAL_ERROR",
                        message="An unexpected error occurred. Our team has been notified.",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        request_id=request_id,
                    )
                ),
            )
