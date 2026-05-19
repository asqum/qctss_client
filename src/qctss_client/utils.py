"""
Utility functions for HTTP requests and retry logic
"""

import time
import logging
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import QCTSSException, QCTSSTimeoutError, map_http_error

logger = logging.getLogger(__name__)

# SDK identification for version checking
try:
    from importlib.metadata import version as _pkg_version

    _SDK_VERSION = _pkg_version("qctss-client")
except Exception:
    _SDK_VERSION = "unknown"
_SDK_NAME = "qctss-client"


class RetryHTTPAdapter(HTTPAdapter):
    """
    HTTP adapter with custom retry logic
    """

    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        # Configure retry strategy (retry only on 5xx and connection errors)
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[500, 502, 503, 504],  # Only retry server errors
            backoff_factor=retry_delay,
            allowed_methods=[
                "HEAD",
                "GET",
                "PUT",
                "DELETE",
                "OPTIONS",
                "TRACE",
                "POST",
            ],
        )
        super().__init__(max_retries=retry_strategy)


def create_session(max_retries: int = 3, retry_delay: int = 5) -> requests.Session:
    """
    Create a requests session with retry configuration

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries in seconds

    Returns:
        Configured requests session
    """
    session = requests.Session()
    adapter = RetryHTTPAdapter(max_retries=max_retries, retry_delay=retry_delay)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def make_request(
    method: str,
    base_url: str,
    endpoint: str,
    token: str,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: int = 5,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> requests.Response:
    """
    Make HTTP request with retry logic and error handling

    Args:
        method: HTTP method (GET, POST, etc.)
        base_url: Base URL for the API
        endpoint: API endpoint path
        token: Authentication token
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries
        data: Request body data
        params: Query parameters
        headers: Additional headers

    Returns:
        Response object

    Raises:
        QCTSSException: On HTTP errors
        TimeoutError: On timeout
    """
    url = urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))

    # Prepare headers
    # According to 2026-01-07 spec: Use X-API-KEY header instead of Authorization Bearer
    request_headers = {
        "X-API-KEY": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-SDK-Name": _SDK_NAME,
        "X-SDK-Version": _SDK_VERSION,
    }
    if headers:
        request_headers.update(headers)

    # Create session with retry logic
    session = create_session(max_retries=max_retries, retry_delay=retry_delay)

    try:
        logger.debug(f"Making {method} request to {url}")

        response = session.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=request_headers,
            timeout=timeout,
        )

        # Handle HTTP errors
        if not response.ok:
            error = map_http_error(response.status_code, response.text)
            logger.error(f"HTTP {response.status_code} error: {response.text}")
            raise error

        logger.debug(f"Request successful: {method} {url} -> {response.status_code}")
        return response

    except requests.exceptions.Timeout as e:
        logger.error(f"Request timeout: {url}")
        raise QCTSSTimeoutError(
            f"Request timed out after {timeout}s",
            details={"url": url, "timeout": timeout},
        ) from e

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {url}")
        raise QCTSSException(
            f"Connection failed to {url}",
            error_code="CONNECTION_ERROR",
            details={"url": url},
        ) from e

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {url} - {str(e)}")
        raise QCTSSException(
            f"Request failed: {str(e)}",
            error_code="REQUEST_ERROR",
            details={"url": url},
        ) from e

    finally:
        session.close()


def get(
    base_url: str,
    endpoint: str,
    token: str,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: int = 5,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience function for GET requests

    Returns:
        Parsed JSON response data
    """
    response = make_request(
        method="GET",
        base_url=base_url,
        endpoint=endpoint,
        token=token,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
        params=params,
    )
    return response.json()


def post(
    base_url: str,
    endpoint: str,
    token: str,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Dict[str, Any]:
    """
    Convenience function for POST requests

    Returns:
        Parsed JSON response data
    """
    response = make_request(
        method="POST",
        base_url=base_url,
        endpoint=endpoint,
        token=token,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
        data=data,
    )
    return response.json()


def put(
    base_url: str,
    endpoint: str,
    token: str,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Dict[str, Any]:
    """
    Convenience function for PUT requests

    Returns:
        Parsed JSON response data
    """
    response = make_request(
        method="PUT",
        base_url=base_url,
        endpoint=endpoint,
        token=token,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
        data=data,
    )
    return response.json()


def delete(
    base_url: str,
    endpoint: str,
    token: str,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Optional[Dict[str, Any]]:
    """
    Convenience function for DELETE requests

    Returns:
        Parsed JSON response data or None if no content
    """
    response = make_request(
        method="DELETE",
        base_url=base_url,
        endpoint=endpoint,
        token=token,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )

    if response.content:
        return response.json()
    return None


def validate_job_id(job_id: int) -> None:
    """Validate job ID parameter

    Args:
        job_id: Job ID to validate

    Raises:
        ValidationError: If job_id is invalid
    """
    from .exceptions import ValidationError

    if not isinstance(job_id, int) or job_id <= 0:
        raise ValidationError("Job ID must be a positive integer")


def validate_qc_setup_list(qc_setup_list) -> None:
    """Validate QC setup list parameter

    Args:
        qc_setup_list: QC setup list to validate

    Raises:
        ValidationError: If qc_setup_list is invalid
    """
    from .exceptions import ValidationError

    if not isinstance(qc_setup_list, list) or len(qc_setup_list) == 0:
        raise ValidationError("QC setup list cannot be empty")

    for item in qc_setup_list:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError("QC setup list items must be non-empty strings")
