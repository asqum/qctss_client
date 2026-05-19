"""
QCTSS Client SDK

A Python SDK for interacting with the QCTSS quantum computing platform.
"""

from .client import QCTSSClient
from .exceptions import (
    QCTSSException,
    ConfigError,
    AuthenticationError,
    AuthorizationError,
    JobClientError,
    JobNotFoundError,
    JobCreationError,
    InvalidJobStateError,
    BillingClientError,
    InvalidBillingPeriodError,
    WebSocketError,
    WebSocketConnectionError,
    WebSocketAuthError,
    ValidationError,
    QCTSSTimeoutError,
    QCSetupNotActiveError,
    QCSetupNotFoundError,
    QCSetupConfigNotFoundError,
)
from .models import JobResponse, JobStatus, BillingData, WebSocketMessage

__version__ = "0.3.0"
SDK_NAME = "qctss-client"


__all__ = [
    "QCTSSClient",
    # Exceptions
    "QCTSSException",
    "ConfigError",
    "AuthenticationError",
    "AuthorizationError",
    "JobClientError",
    "JobNotFoundError",
    "JobCreationError",
    "InvalidJobStateError",
    "BillingClientError",
    "InvalidBillingPeriodError",
    "WebSocketError",
    "WebSocketConnectionError",
    "WebSocketAuthError",
    "ValidationError",
    "QCTSSTimeoutError",
    "QCSetupNotActiveError",
    "QCSetupNotFoundError",
    "QCSetupConfigNotFoundError",
    # Models
    "JobResponse",
    "JobStatus",
    "BillingData",
    "WebSocketMessage",
]
