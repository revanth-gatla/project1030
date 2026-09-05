"""Structured application error types mapped to HTTP responses."""

from __future__ import annotations


class AppError(Exception):
    """Base application error."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "An unexpected error occurred.", *, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class AuthenticationError(AppError):
    status_code = 401
    code = "AUTHENTICATION_ERROR"


class AuthorizationError(AppError):
    status_code = 403
    code = "AUTHORIZATION_ERROR"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class FileValidationError(AppError):
    status_code = 422
    code = "FILE_VALIDATION_ERROR"


class ExtractionError(AppError):
    status_code = 502
    code = "EXTRACTION_ERROR"


class AIProviderError(AppError):
    status_code = 502
    code = "AI_PROVIDER_ERROR"


class ProcessingError(AppError):
    status_code = 500
    code = "PROCESSING_ERROR"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT_ERROR"


class RateLimitError(AppError):
    status_code = 429
    code = "RATE_LIMIT_ERROR"


class UploadFailedError(AppError):
    status_code = 400
    code = "UPLOAD_FAILED"


class PdfTextExtractionFailedError(AppError):
    status_code = 422
    code = "PDF_TEXT_EXTRACTION_FAILED"


class EmptyPdfTextError(AppError):
    status_code = 422
    code = "EMPTY_PDF_TEXT"


class StructuredExtractionFailedError(AppError):
    status_code = 502
    code = "STRUCTURED_EXTRACTION_FAILED"


class NoLabParametersFoundError(AppError):
    status_code = 422
    code = "NO_LAB_PARAMETERS_FOUND"


class DatabasePersistenceFailedError(AppError):
    status_code = 500
    code = "DATABASE_PERSISTENCE_FAILED"
