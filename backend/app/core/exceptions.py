from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.logging import logger


class EduVaultException(Exception):
    """Base exception for EduVault application errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class EntityNotFoundException(EduVaultException):
    """Raised when a requested resource does not exist."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class AuthenticationException(EduVaultException):
    """Raised when credentials or tokens are invalid."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationException(EduVaultException):
    """Raised when user has insufficient permissions."""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class DuplicateResourceException(EduVaultException):
    """Raised when creating a resource that already exists."""
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class ValidationException(EduVaultException):
    """Raised for business logic validation errors."""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class StorageException(EduVaultException):
    """Raised when object store or vector store operations fail."""
    def __init__(self, message: str = "Storage operation failed"):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IngestionException(EduVaultException):
    """Raised when document ingestion or parsing fails."""
    def __init__(self, message: str = "Document ingestion failed"):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def register_exception_handlers(app: FastAPI) -> None:
    """Registers standard exception handlers on the FastAPI application."""

    @app.exception_handler(EduVaultException)
    async def eduvault_exception_handler(request: Request, exc: EduVaultException):
        logger.warning(f"EduVaultException on {request.method} {request.url.path}: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"RequestValidationError on {request.method} {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected server error occurred."},
        )
