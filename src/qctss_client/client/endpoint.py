"""QCTSS Client endpoint management (:mod:`qctss_client.client.endpoint`)"""

from typing import Literal, Any
from urllib.parse import urlparse
from dataclasses import dataclass
from pathlib import Path
import logging
import json

from ..exceptions import TokenExistingWarning, TokenNotFoundError

logger = logging.getLogger(__name__)

AvailableCategory = Literal["internal"]
"""The available backend URL categories for QCTSS Client.

- internal: The internal backend URL for the QC-Test Space.
    This will require you have VPN access to the internal network.
    Please contact the QC-Test Space team for access if you are an authorized user.
"""
UrlDict = dict[AvailableCategory, str]

DEFAULT_URL_CATEGORY: AvailableCategory = "internal"
"""Default backend URL category for QCTSS Client.
This is set to 'internal' for internal network access.

- internal: The internal backend URL for the QC-Test Space.
    This will require you have VPN access to the internal network.
    Please contact the QC-Test Space team for access if you are an authorized user.
"""

BACKEND_URLS: UrlDict = {"internal": "http://10.21.19.201:80/"}
"""The all available backend URL for the QC-Test Space. """

FASTAPI_URLS: UrlDict = {"internal": "http://10.21.19.201:80/"}
"""The all available FastAPI URL for the QC-Test Space. """

WEBSOCKET_URLS: UrlDict = {"internal": "ws://10.21.19.201:80/"}
"""The all available WebSocket URL for the QC-Test Space. """


@dataclass(frozen=True)
class BackendConfig:
    """Configuration for QCTSS backend connection

    This class provides configuration management with build-time backend URL injection.
    No environment files are required as the backend URL is embedded during build.

    Args:
        backend_url (str): Backend server URL
        fastapi_url (str): FastAPI server URL
        websocket_url (str): WebSocket server URL
        timeout (int): Request timeout in seconds. Default is 30 seconds.
        max_retries (int): Maximum number of retries for failed requests. Default is 3.
        retry_delay (int): Delay between retries in seconds. Default is 5 seconds.
    """

    backend_url: str = BACKEND_URLS[DEFAULT_URL_CATEGORY]
    fastapi_url: str = FASTAPI_URLS[DEFAULT_URL_CATEGORY]
    websocket_url: str = WEBSOCKET_URLS[DEFAULT_URL_CATEGORY]
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5

    def __post_init__(self):
        """Validate configuration parameters after initialization"""

        parsed = urlparse(self.backend_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid backend URL format: {self.backend_url}")

        # Validate numeric parameters
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.retry_delay < 0:
            raise ValueError("Retry delay cannot be negative")

        logger.info(
            f"QCTSS Client configured with backend: {self.backend_url}"
            + f", FastAPI: {self.fastapi_url}, WebSocket: {self.websocket_url}"
        )

    def get_api_url(self, endpoint: str) -> str:
        """Get full API URL for an endpoint

        Args:
            endpoint (str):
                API endpoint path (e.g., 'https://api-domain/endpoint/')

        Returns:
            Full API URL
        """
        base_url = self.backend_url.rstrip("/")
        endpoint = endpoint.lstrip("/")
        return f"{base_url}/{endpoint}"

    def get_fastapi_url(self, endpoint: str) -> str:
        """Get FastAPI URL for a specific endpoint

        Args:
            endpoint (str):
                FastAPI endpoint path (e.g., 'https://fastapi-domain/endpoint/')

        Returns:
            Full FastAPI URL
        """
        base_url = self.fastapi_url.rstrip("/")
        endpoint = endpoint.lstrip("/")
        return f"{base_url}/{endpoint}"

    def get_websocket_url(self, endpoint: str) -> str:
        """Get WebSocket URL for a specific endpoint

        Args:
            endpoint (str):
                WebSocket endpoint path (e.g., 'wss://websocket-domain/endpoint/')

        Returns:
            Full WebSocket URL
        """
        base_url = self.websocket_url.rstrip("/")
        endpoint = endpoint.lstrip("/")
        return f"{base_url}/{endpoint}"

    def __repr__(self) -> str:
        """Custom representation for debugging"""
        return (
            f"BackendConfig(backend_url={self.backend_url}, "
            f"fastapi_url={self.fastapi_url}, "
            f"websocket_url={self.websocket_url}, "
            f"timeout={self.timeout}, "
            f"max_retries={self.max_retries}, "
            f"retry_delay={self.retry_delay})"
        )

    def _repr_pretty_(self, p: Any, cycle: bool) -> None:
        """Render a compact multiline representation in IPython/Jupyter."""
        if cycle:
            p.text(f"{self.__class__.__name__}(...)")
            return

        p.begin_group(2, f"{self.__class__.__name__}(")
        p.breakable()
        p.text(f"backend_url={self.backend_url},")
        p.breakable()
        p.text(f"fastapi_url={self.fastapi_url},")
        p.breakable()
        p.text(f"websocket_url={self.websocket_url},")
        p.breakable()
        p.text(f"timeout={self.timeout},")
        p.breakable()
        p.text(f"max_retries={self.max_retries},")
        p.breakable()
        p.text(f"retry_delay={self.retry_delay}")
        p.end_group(2, ")")


DEFAULT_CONFIG = BackendConfig()
"""Default configuration instance for QCTSS Client. """

DEFAULT_QCTSS_CONFIG_PATH = Path.home() / ".qctss"
"""Default path for QCTSS configuration files (~/.qctss)"""

DEFAULT_TOKEN_FILE_NAME = "qctss-client.json"
"""Default token file name for QCTSS Client (qctss-client.json)"""

DEFAULT_CHANNEL_NAME = "default"
"""Default channel name for QCTSS Client token storage (default)"""


def read_token(
    channel_name: str = DEFAULT_CHANNEL_NAME, path: Path = DEFAULT_QCTSS_CONFIG_PATH
) -> dict[str, str]:
    """Read the token from a file in the specified path.

    Args:
        channel_name (str): The channel name associated with the token.
            Default is "default".
        path (Path): The directory path where the token file is located.
            Defaults to ~/.qctss

    Returns:
        dict[str, str]: A dictionary containing the token and endpoint category.

    Raises:
        TokenNotFoundError: If the token file or the token for the specified channel is not found.
    """

    token_file_path = path / DEFAULT_TOKEN_FILE_NAME
    if not token_file_path.exists():
        raise TokenNotFoundError(
            f"Token file not found at {token_file_path}. "
            "Please ensure the token is saved using save_token()."
        )
    with open(token_file_path, "r") as f:
        config_data = json.load(f)

    if channel_name not in config_data:
        raise TokenNotFoundError(
            f"Token for channel '{channel_name}' not found in {token_file_path}. "
            "Please ensure the token is saved using save_token()."
        )

    required_keys = {"token", "endpoint_category"}
    if not required_keys.issubset(config_data[channel_name].keys()):
        raise TokenNotFoundError(
            f"Token for channel '{channel_name}' is missing required keys in {token_file_path}. "
            "Please ensure the token is saved using save_token()."
        )
    return config_data.get(channel_name, {})


def save_token(
    token: str,
    channel_name: str = DEFAULT_CHANNEL_NAME,
    endpoint_category: AvailableCategory = DEFAULT_URL_CATEGORY,
    path: Path = DEFAULT_QCTSS_CONFIG_PATH,
    replace: bool = False,
) -> None:
    """Save the token to a file in the specified path.

    Args:
        token (str): The token string to save.
        channel_name (str): The channel name associated with the token.
            Default is "default".
        endpoint_category (AvailableCategory): Category of the endpoint URLs.
            Default is the default URL category.
        path (Path): The directory path where the token file will be saved.
            Defaults to ~/.qctss
        replace (bool): If True, replace the existing token for the channel.
            If False, give a warning if the token for the channel already exists.
            Default is False.
    """

    path.mkdir(parents=True, exist_ok=True)
    token_file_path = path / DEFAULT_TOKEN_FILE_NAME
    with open(token_file_path, "w+") as f:
        config_data = (
            json.load(f)
            if token_file_path.exists() and token_file_path.stat().st_size > 0
            else {}
        )
        if channel_name in config_data and not replace:
            logger.warning(
                f"Token for channel '{channel_name}' already exists. "
                "Use 'replace=True' to overwrite it."
            )
            raise TokenExistingWarning(
                f"Token for channel '{channel_name}' already exists. "
                "Use 'replace=True' to overwrite it."
            )
        config_data[channel_name] = {
            "token": token,
            "endpoint_category": endpoint_category,
        }
        f.seek(0)
        json.dump(config_data, f, indent=2)
    logger.info(f"Token saved to {token_file_path}")
