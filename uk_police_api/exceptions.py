"""Custom exceptions for the UK Police API client."""

from __future__ import annotations


class PoliceAPIError(Exception):
    """Base exception for all UK Police API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class PoliceAPINotFoundError(PoliceAPIError):
    """Resource not found (HTTP 404)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class PoliceAPIRateLimitError(PoliceAPIError):
    """Rate limited by the API after all retries exhausted (HTTP 429)."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class PoliceAPIServerError(PoliceAPIError):
    """API server error (HTTP 5xx)."""

    def __init__(self, message: str = "Server error", status_code: int = 500):
        super().__init__(message, status_code=status_code)


class PoliceAPITimeoutError(PoliceAPIError):
    """Request timed out."""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message, status_code=None)


class PoliceAPIResponseError(PoliceAPIError):
    """Invalid or unparseable response from the API."""

    def __init__(self, message: str = "Invalid response from API"):
        super().__init__(message, status_code=None)
