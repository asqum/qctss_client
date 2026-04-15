"""
QCTSS Client SDK

A Python SDK for interacting with the QCTSS quantum computing platform.
"""

__version__ = "0.2.0"
SDK_NAME = "qctss-client"
__author__ = "Quantaser Photonics Co. Ltd."
__email__ = "tina@quantaser.com"

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
    "SDK_NAME",
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