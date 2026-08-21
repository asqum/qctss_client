"""Exception hierarchy for QCTSS Client SDK (:mod:`qctss_client.exceptions`)

- Exception Hierarchy

.. code-block:: text

    Exception
    └── QCTSSException (base)
        ├── ConfigError
        ├── AuthenticationError
        │   ├── TokenExistingWarning (also inherits from Warning)
        │   └── TokenNotFoundError (also inherits from FileNotFoundError)
        ├── AuthorizationError
        ├── JobClientError
        │   ├── JobNotFoundError
        │   ├── JobCreationError
        │   ├── InvalidJobStateError
        │   └── JobFailedError
        ├── BillingClientError
        │   └── InvalidBillingPeriodError
        ├── WebSocketError
        │   ├── WebSocketConnectionError
        │   └── WebSocketAuthError
        ├── ValidationError (also inherits from ValueError)
        ├── QCSetupException (base for QCSetup-related errors)
        │   ├── QCSetupNotActiveError
        │   ├── QCSetupNotFoundError
        │   └── QCSetupConfigNotFoundError
        ├── QCTSSTimeoutError (also inherits from TimeoutError)
        └── InvalidPackageInfo (also inherits from Warning)

"""

from typing import Optional, Any, Literal
from enum import Enum
import json

ErrorCodeType = Literal[
    "TIMEOUT_ERROR",
    "CONNECTION_ERROR",
    "REQUEST_ERROR",
    "CLIENT_ERROR",
    "SERVER_ERROR",
    "UNAUTHORIZED",
    "FORBIDDEN",
    "NOT_FOUND",
    "VALIDATION_ERROR",
    "HTTP_ERROR",
]


class ErrorCode(Enum):
    """Enumeration of error codes for QCTSS Client exceptions."""

    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    """Indicates that an operation timed out."""
    CONNECTION_ERROR = "CONNECTION_ERROR"
    """Indicates a connection-related error (e.g., network issues)."""
    REQUEST_ERROR = "REQUEST_ERROR"
    """Indicates an error related to the request (e.g., malformed request)."""
    CLIENT_ERROR = "CLIENT_ERROR"
    """Indicates a client-side error (HTTP 4xx)."""
    SERVER_ERROR = "SERVER_ERROR"
    """Indicates a server-side error (HTTP 5xx)."""
    UNAUTHORIZED = "UNAUTHORIZED"
    """Indicates that authentication failed (HTTP 401)."""
    FORBIDDEN = "FORBIDDEN"
    """Indicates that the user does not have permission (HTTP 403)."""
    NOT_FOUND = "NOT_FOUND"
    """Indicates that the requested resource was not found (HTTP 404)."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    """Indicates that input validation failed (HTTP 422)."""
    HTTP_ERROR = "HTTP_ERROR"
    """Indicates a generic HTTP error not covered by other codes."""


class QCTSSException(Exception):
    """Base exception for all QCTSS Client errors."""

    message: str
    """Error message describing the exception."""
    http_status: Optional[int]
    """HTTP status code associated with the error (if applicable)."""
    error_code: Optional[ErrorCode]
    """Specific error code for categorizing the exception."""
    backend_message: Optional[str]
    """Message returned from the backend (if applicable)."""
    details: dict[str, Any]
    """Additional details about the error (if applicable),
    usually parsed from the backend response."""

    def __init__(
        self,
        message: str,
        http_status: Optional[int] = None,
        error_code: Optional[ErrorCode] = None,
        backend_message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.error_code: Optional[ErrorCode] = error_code
        self.backend_message = backend_message
        self.details = details if details is not None else {}

    def __repr__(self) -> str:
        parts = [str(self.message)]
        if self.http_status:
            parts.append(f'HTTP "{self.http_status}"')
        if self.error_code:
            parts.append(f'Code: "{self.error_code}"')
        if self.backend_message:
            parts.append(f'Backend: "{self.backend_message}"')
        return " | ".join(parts)

    def __str__(self) -> str:
        return self.__repr__()


class ConfigError(QCTSSException):
    """Configuration-related errors"""


# Authentication and authorization exceptions
class AuthenticationError(QCTSSException):
    """Authentication failed (invalid token, expired, etc.)"""


class TokenExistingWarning(AuthenticationError, Warning):
    """Warning when an existing token is found in the config file"""


class TokenNotFoundError(AuthenticationError, FileNotFoundError):
    """Token not found in the config file"""


class AuthorizationError(QCTSSException):
    """Authorization failed (insufficient permissions)"""


# Job-related exceptions
class JobClientError(QCTSSException):
    """General job-related client errors"""


class JobNotFoundError(JobClientError):
    """Specific job not found"""


class JobCreationError(JobClientError):
    """Job creation failed"""


class InvalidJobStateError(JobClientError):
    """Job is in invalid state for requested operation"""


class JobFailedError(JobClientError):
    """Job ended in a terminal failure state (cancelled/failed/timeout)"""


# Billing-related exceptions
class BillingClientError(QCTSSException):
    """Billing-related errors"""


class InvalidBillingPeriodError(BillingClientError):
    """Invalid billing period specified"""


class WebSocketError(QCTSSException):
    """WebSocket-related errors"""


# Specific WebSocket exceptions
class WebSocketConnectionError(WebSocketError):
    """WebSocket connection failed"""


class WebSocketAuthError(WebSocketError):
    """WebSocket authentication failed"""


# Validation and QCSetup-related exceptions
class ValidationError(QCTSSException, ValueError):
    """Input validation errors"""


class QCSetupException(QCTSSException):
    """Base exception for QCSetup-related errors"""


class QCSetupNotActiveError(QCSetupException):
    """The specified QCSetup exists but is not currently active (no activated config)"""


class QCSetupNotFoundError(QCSetupException):
    """The specified QCSetup does not exist"""


class QCSetupConfigNotFoundError(QCSetupException):
    """The specified QCSetup exists but has no activated config"""


class QCTSSTimeoutError(QCTSSException, TimeoutError):
    """Operation timed out"""


def map_http_error(status_code: int, response_text: str = "") -> QCTSSException:
    """Map HTTP status codes to appropriate SDK exceptions

    Args:
        status_code: HTTP status code
        response_text: Response body text

    Returns:
        Appropriate QCTSSException subclass
    """

    exception_map = {
        401: (AuthenticationError, "Authentication failed", "UNAUTHORIZED"),
        403: (AuthorizationError, "Access denied", "FORBIDDEN"),
        404: (JobNotFoundError, "Resource not found", "NOT_FOUND"),
        422: (ValidationError, "Validation failed", "VALIDATION_ERROR"),
    }

    try:
        error_response = json.loads(response_text)
        if isinstance(error_response, dict):
            error_details = error_response
        else:
            error_details = {"response": error_response}
    except json.JSONDecodeError:
        # If response is not valid JSON, we can ignore and proceed with the raw text
        error_details = {"response": response_text}

    backend_message = (
        error_details.pop("error") if "error" in error_details else response_text
    )

    if status_code in exception_map:
        exc_class, message, error_code = exception_map[status_code]
        return exc_class(
            message,
            http_status=status_code,
            error_code=error_code,
            backend_message=backend_message,
            details=error_details,
        )

    if 400 <= status_code < 500:
        return JobClientError(
            f"Client error: {status_code}",
            http_status=status_code,
            error_code=ErrorCode.CLIENT_ERROR,
            backend_message=backend_message,
            details=error_details,
        )

    if 500 <= status_code < 600:
        return QCTSSException(
            f"Server error: {status_code}",
            http_status=status_code,
            error_code=ErrorCode.SERVER_ERROR,
            backend_message=backend_message,
            details=error_details,
        )

    return QCTSSException(
        f"HTTP error: {status_code}",
        http_status=status_code,
        error_code=ErrorCode.HTTP_ERROR,
        backend_message=backend_message,
        details=error_details,
    )


class InvalidPackageInfo(QCTSSException, Warning):
    """Raised when package information cannot be retrieved or is invalid"""
