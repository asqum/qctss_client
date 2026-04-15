"""
Exception hierarchy for QCTSS Client SDK
"""
from typing import Optional, Dict, Any


class QCTSSException(Exception):
    """
    Base exception for all QCTSS Client errors
    """
    
    def __init__(
        self,
        message: str,
        http_status: Optional[int] = None,
        error_code: Optional[str] = None,
        backend_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.error_code = error_code
        self.backend_message = backend_message
        self.details = details or {}
    
    def __str__(self) -> str:
        parts = [self.message]
        
        if self.http_status:
            parts.append(f"HTTP {self.http_status}")
        
        if self.error_code:
            parts.append(f"Code: {self.error_code}")
            
        if self.backend_message:
            parts.append(f"Backend: {self.backend_message}")
        
        return " | ".join(parts)


class ConfigError(QCTSSException):
    """Configuration-related errors"""
    pass


class AuthenticationError(QCTSSException):
    """Authentication failed (invalid token, expired, etc.)"""
    pass


class AuthorizationError(QCTSSException):
    """Authorization failed (insufficient permissions)"""
    pass


class JobClientError(QCTSSException):
    """General job-related client errors"""
    pass


class JobNotFoundError(JobClientError):
    """Specific job not found"""
    pass


class JobCreationError(JobClientError):
    """Job creation failed"""
    pass


class InvalidJobStateError(JobClientError):
    """Job is in invalid state for requested operation"""
    pass


class BillingClientError(QCTSSException):
    """Billing-related errors"""
    pass


class InvalidBillingPeriodError(BillingClientError):
    """Invalid billing period specified"""
    pass


class WebSocketError(QCTSSException):
    """WebSocket-related errors"""
    pass


class WebSocketConnectionError(WebSocketError):
    """WebSocket connection failed"""
    pass


class WebSocketAuthError(WebSocketError):
    """WebSocket authentication failed"""
    pass


class ValidationError(QCTSSException):
    """Input validation errors"""
    pass


class TimeoutError(QCTSSException):
    """Request timeout errors"""
    pass


class QCSetupNotActiveError(QCTSSException):
    """QCSetup 狀態非 active"""
    pass


class QCSetupNotFoundError(QCTSSException):
    """QCSetup 不存在"""
    pass


def map_http_error(status_code: int, response_text: str = "") -> QCTSSException:
    """
    Map HTTP status codes to appropriate SDK exceptions
    
    Args:
        status_code: HTTP status code
        response_text: Response body text
        
    Returns:
        Appropriate QCTSSException subclass
    """
    error_details = {"status_code": status_code, "response": response_text}
    
    if status_code == 401:
        return AuthenticationError(
            "Authentication failed",
            http_status=status_code,
            error_code="UNAUTHORIZED",
            backend_message=response_text,
            details=error_details
        )
    
    elif status_code == 403:
        return AuthorizationError(
            "Access denied",
            http_status=status_code,
            error_code="FORBIDDEN",
            backend_message=response_text,
            details=error_details
        )
    
    elif status_code == 404:
        return JobNotFoundError(
            "Resource not found", 
            http_status=status_code,
            error_code="NOT_FOUND",
            backend_message=response_text,
            details=error_details
        )
    
    elif status_code == 422:
        return ValidationError(
            "Validation failed",
            http_status=status_code,
            error_code="VALIDATION_ERROR", 
            backend_message=response_text,
            details=error_details
        )
    
    elif 400 <= status_code < 500:
        return JobClientError(
            f"Client error: {status_code}",
            http_status=status_code,
            error_code="CLIENT_ERROR",
            backend_message=response_text,
            details=error_details
        )
    
    elif 500 <= status_code < 600:
        return QCTSSException(
            f"Server error: {status_code}",
            http_status=status_code,
            error_code="SERVER_ERROR",
            backend_message=response_text,
            details=error_details
        )
    
    else:
        return QCTSSException(
            f"HTTP error: {status_code}",
            http_status=status_code,
            error_code="HTTP_ERROR", 
            backend_message=response_text,
            details=error_details
        )