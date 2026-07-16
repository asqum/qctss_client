"""HTTP requests and retry logic (:mod:`qctss_client.utils.http`)"""

import logging
from typing import Any, Optional
from urllib.parse import urljoin
from urllib3.util.retry import Retry
import requests
from requests.adapters import HTTPAdapter

from .other import SDK_NAME, SDK_VERSION
from ..exceptions import (
    QCTSSException,
    QCTSSTimeoutError,
    map_http_error,
)

logger = logging.getLogger(__name__)


class RetryHTTPAdapter(HTTPAdapter):
    """HTTP adapter with custom retry logic.

    This adapter retries requests on server errors (5xx) and connection errors,
    with a configurable number of retries and delay between retries.

    Args:
        max_retries (int): Maximum number of retry attempts. Default is 3.
        retry_delay (int): Base delay between retries in seconds. Default is 5.
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
    """Create a requests session with retry configuration

    Args:
        max_retries (int): Maximum number of retry attempts. Default is 3.
        retry_delay (int): Base delay between retries in seconds. Default is 5.

    Returns:
        requests.Session: Configured requests session
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
    data: Optional[dict[str, Any]] = None,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, str]] = None,
) -> requests.Response:
    """Make HTTP request with retry logic and error handling

    Args:
        method (str): HTTP method (GET, POST, etc.)
        base_url (str): Base URL for the API
        endpoint (str): API endpoint path
        token (str): Authentication token
        timeout (int): Request timeout in seconds
        max_retries (int): Maximum retry attempts. Default is 3.
        retry_delay (int): Delay between retries in seconds. Default is 5.
        data (Optional[dict[str, Any]]): Request body data
        params (Optional[dict[str, Any]]): Query parameters
        headers (Optional[dict[str, str]]): Additional headers

    Returns:
        requests.Response: Response object

    Raises:
        QCTSSException: On HTTP errors
        QCTSSTimeoutError: On timeout
    """
    url = urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))

    # Prepare headers
    # According to 2026-01-07 spec: Use X-API-KEY header instead of Authorization Bearer
    request_headers = {
        "X-API-KEY": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-SDK-Name": SDK_NAME,
        "X-SDK-Version": SDK_VERSION,
    }
    if headers:
        request_headers.update(headers)

    # Create session with retry logic
    session = create_session(max_retries=max_retries, retry_delay=retry_delay)

    try:
        logger.debug("Making %s request to %s", method, url)

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
            logger.error("HTTP %s error: %s", response.status_code, response.text)
            raise error

        logger.debug(
            "Request successful: %s %s -> %s", method, url, response.status_code
        )
        return response

    except requests.exceptions.Timeout as e:
        logger.error("Request timeout: %s", url)
        raise QCTSSTimeoutError(
            f"Request timed out after {timeout}s",
            details={"url": url, "timeout": timeout},
        ) from e

    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error: %s", url)
        raise QCTSSException(
            f"Connection failed to {url}",
            error_code="CONNECTION_ERROR",
            details={"url": url},
        ) from e

    except requests.exceptions.RequestException as e:
        logger.error("Request error: %s - %s", url, str(e))
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
    params: Optional[dict[str, Any]] = None,
) -> Any:
    """Convenience function for GET requests

    Args:
        base_url (str): Base URL for the API
        endpoint (str): API endpoint path
        token (str): Authentication token
        timeout (int): Request timeout in seconds
        max_retries (int): Maximum retry attempts. Default is 3.
        retry_delay (int): Delay between retries in seconds. Default is 5.
        params (Optional[dict[str, Any]]): Query parameters. Default is None.

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
    data: Optional[dict[str, Any]] = None,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Any:
    """Convenience function for POST requests

    Args:
        base_url (str): Base URL for the API
        endpoint (str): API endpoint path
        token (str): Authentication token
        data (Optional[dict[str, Any]]): Request body data. Default is None.
        timeout (int): Request timeout in seconds. Default is 30.
        max_retries (int): Maximum retry attempts. Default is 3.
        retry_delay (int): Delay between retries in seconds. Default is 5.

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
    data: Optional[dict[str, Any]] = None,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Any:
    """Convenience function for PUT requests

    Args:
        base_url (str): Base URL for the API
        endpoint (str): API endpoint path
        token (str): Authentication token
        data (Optional[dict[str, Any]]): Request body data. Default is None.
        timeout (int): Request timeout in seconds. Default is 30.
        max_retries (int): Maximum retry attempts. Default is 3.
        retry_delay (int): Delay between retries in seconds. Default is 5.

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
) -> Optional[Any]:
    """Convenience function for DELETE requests

    Args:
        base_url (str): Base URL for the API
        endpoint (str): API endpoint path
        token (str): Authentication token
        timeout (int): Request timeout in seconds. Default is 30.
        max_retries (int): Maximum retry attempts. Default is 3.
        retry_delay (int): Delay between retries in seconds. Default is 5.

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
