"""
QCTSS Client SDK

A Python SDK for interacting with the QCTSS quantum computing platform.
"""

__version__ = "0.1.0"
__author__ = "QCTSS Team"
__email__ = "dev@qctss.com"

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
    TimeoutError,
)
from .models import JobResponse, JobStatus, BillingData, WebSocketMessage

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
    "TimeoutError",
    # Models
    "JobResponse",
    "JobStatus", 
    "BillingData",
    "WebSocketMessage",
]