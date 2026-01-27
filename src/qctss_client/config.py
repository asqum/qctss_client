"""
Configuration management for QCTSS Client

This module provides configuration management without relying on environment files.
The DEFAULT_BACKEND_URL is written at build time by the build script.
"""
from typing import Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# DEFAULT_BACKEND_URL will be written by build_script.py during package building
# DO NOT modify this manually - it will be overwritten during build process
DEFAULT_BACKEND_URL = "http://10.21.19.201:80"

# DEFAULT_FASTAPI_URL will be written by build_script.py during package building
# DO NOT modify this manually - it will be overwritten during build process
DEFAULT_FASTAPI_URL = "ws://10.21.19.201:80"


class BackendConfig:
    """
    Configuration for QCTSS backend connection
    
    This class provides configuration management with build-time backend URL injection.
    No environment files are required as the backend URL is embedded during build.
    """
    
    def __init__(
        self,
        backend_url: Optional[str] = None,
        fastapi_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
    ):
        """
        Initialize configuration with build-time defaults
        
        Args:
            backend_url: Backend server URL (defaults to build-time configured URL)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 5)
        """
        # Use build-time configured URL as default
        self.backend_url = backend_url or DEFAULT_BACKEND_URL
        self.fastapi_url = fastapi_url or DEFAULT_FASTAPI_URL
        self.timeout = timeout or 30
        self.max_retries = max_retries or 3
        self.retry_delay = retry_delay or 5
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"RCCI Client configured with backend: {self.backend_url}")
    
    def _validate_config(self) -> None:
        """Validate configuration parameters"""
        # Validate backend URL
        if not self.backend_url:
            raise ValueError("Backend URL cannot be empty")
        
        try:
            parsed = urlparse(self.backend_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid backend URL format: {self.backend_url}")
        except Exception as e:
            raise ValueError(f"Invalid backend URL: {e}")
        
        # Validate numeric parameters
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.retry_delay < 0:
            raise ValueError("Retry delay cannot be negative")
    
    def get_api_url(self, endpoint: str) -> str:
        """
        Get full API URL for an endpoint
        
        Args:
            endpoint: API endpoint path (e.g., '/jobs/')
            
        Returns:
            Full API URL
        """
        base_url = self.backend_url.rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{base_url}/{endpoint}"
    
    def get_websocket_url(self) -> str:
        """
        Get WebSocket base URL for FastAPI WebSocket connection
        
        Returns:
            WebSocket base URL for FastAPI server
        """
        # Use dedicated FastAPI URL instead of deriving from backend URL
        return self.fastapi_url
    
    @property
    def websocket_url(self) -> str:
        """Get WebSocket URL from HTTP URL (property for backward compatibility)"""
        return self.get_websocket_url()
    
    def __repr__(self) -> str:
        return (f"BackendConfig(backend_url='{self.backend_url}', "
                f"timeout={self.timeout}, max_retries={self.max_retries}, "
                f"retry_delay={self.retry_delay})")


# Global default configuration instance
default_config = BackendConfig()


def get_default_config() -> BackendConfig:
    """
    Get the default configuration instance
    
    Returns:
        Default BackendConfig instance
    """
    return default_config


def create_config(**kwargs) -> BackendConfig:
    """
    Create a new configuration instance with custom parameters
    
    Args:
        **kwargs: Configuration parameters for BackendConfig
        
    Returns:
        New BackendConfig instance
    """
    return BackendConfig(**kwargs)

# Alias for backward compatibility with tests
RCCIConfig = BackendConfig