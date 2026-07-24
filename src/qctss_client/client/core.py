"""QCTSS Client Core. (:mod:`qctss_client.client.core`)"""

from typing import Optional, Callable, Any
from pathlib import Path
import logging
import requests

from .endpoint import (
    BackendConfig,
    save_token,
    read_token,
    list_available_channels,
    DEFAULT_CHANNEL_NAME,
    DEFAULT_URL_CATEGORY,
    AvailableCategory,
)
from .subscribe import JobWaitingMonitor, MAX_TIMEOUT
from ..exceptions import (
    QCTSSException,
    ValidationError,
    QCSetupConfigNotFoundError,
    QCSetupNotActiveError,
    QCSetupNotFoundError,
    JobFailedError,
    JobCreationError,
    InvalidJobStateError,
)
from ..models import JobResponse, JobStatus
from ..websocket_manager import WebSocketManager
from ..utils import http, validate_job_id

logger = logging.getLogger(__name__)


class QCTSSClient:
    """Main client class for interacting with QCTSS backend."""

    @staticmethod
    def save_token(
        token: str,
        channel_name: str = DEFAULT_CHANNEL_NAME,
        endpoint_category: AvailableCategory = DEFAULT_URL_CATEGORY,
        replace: bool = False,
    ):
        """Save the token to the default config path (~/.qctss/qctss-client.json).

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
        save_token(
            token,
            channel_name=channel_name,
            endpoint_category=endpoint_category,
            replace=replace,
        )

    @property
    def token(self) -> str:
        """Get the current token for the client.

        Returns:
            str: The current token value.
        """
        return self._token

    @token.setter
    def token(self, value: str):
        """Set the token for the client.

        Args:
            value (str): The new token value.
        """
        if not value or not isinstance(value, str):
            raise ValidationError("Token must be a non-empty string")

        self._token = value

    @staticmethod
    def list_channels() -> list[str]:
        """List all available channels with saved tokens.

        Returns:
            list[str]: List of channel names.
        """
        return list_available_channels()

    def __init__(
        self,
        channel_name: str = DEFAULT_CHANNEL_NAME,
        backend_url: Optional[str] = None,
        fastapi_url: Optional[str] = None,
        websocket_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
    ):
        """Initialize QCTSS Client.

        Args:
            channel_name (str): Channel name to read token from config file.
            backend_url (Optional[str]): Backend server URL
            fastapi_url (Optional[str]): FastAPI server URL
            websocket_url (Optional[str]): WebSocket server URL
            timeout (Optional[int]):
                Request timeout in seconds. Default is 30 seconds.
            max_retries (Optional[int]):
                Maximum number of retries for failed requests. Default is 3.
            retry_delay (Optional[int]):
                Delay between retries in seconds. Default is 5 seconds.

        Raises:
            ValidationError: If token is empty or None
        """

        token_info = read_token(channel_name=channel_name)
        token = token_info.get("token")
        if not token:
            raise ValidationError("Token cannot be empty")
        self.token = token

        config_args: dict[str, Any] = {"channel_name": channel_name}
        if backend_url:
            config_args["backend_url"] = backend_url
        if fastapi_url:
            config_args["fastapi_url"] = fastapi_url
        if websocket_url:
            config_args["websocket_url"] = websocket_url
        if timeout is not None:
            config_args["timeout"] = timeout
        if max_retries is not None:
            config_args["max_retries"] = max_retries
        if retry_delay is not None:
            config_args["retry_delay"] = retry_delay
        self.config = BackendConfig(**config_args)

        self._websocket_connections: dict[int, Any] = {}
        self._websocket_manager = WebSocketManager()

        logger.info(f"Initialized QCTSS Client for {self.config.backend_url}")

    def _get(self, endpoint: str, params: Optional[dict[str, Any]] = None):
        """Make GET request to backend API (Django).

        Args:
            endpoint (str): API endpoint path
            params (Optional[dict[str, Any]]): Query parameters

        Returns:
            JSON response data
        """
        return http.get(
            base_url=self.config.backend_url,
            endpoint=endpoint,
            token=self._token,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            params=params,
        )

    def _get_fastapi(self, endpoint: str, params: Optional[dict[str, Any]] = None):
        """Make GET request to FastAPI server.

        Args:
            endpoint (str): API endpoint path
            params (Optional[dict[str, Any]]): Query parameters

        Returns:
            JSON response data
        """
        return http.get(
            base_url=self.config.fastapi_url,
            endpoint=endpoint,
            token=self._token,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            params=params,
        )

    def _post(self, endpoint: str, data: Optional[dict[str, Any]] = None) -> Any:
        """Make POST request to backend API.

        Args:
            endpoint (str): API endpoint path
            data (Optional[dict[str, Any]]): Request body data

        Returns:
            JSON response data
        """
        return http.post(
            base_url=self.config.backend_url,
            endpoint=endpoint,
            token=self._token,
            data=data,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
        )

    def _put(self, endpoint: str, data: Optional[dict[str, Any]] = None) -> Any:
        """Make PUT request to backend API.

        Args:
            endpoint (str): API endpoint path
            data (Optional[dict[str, Any]]): Request body data

        Returns:
            JSON response data
        """
        return http.put(
            base_url=self.config.backend_url,
            endpoint=endpoint,
            token=self._token,
            data=data,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
        )

    def _delete(self, endpoint: str) -> Optional[Any]:
        """Make DELETE request to backend API.

        Args:
            endpoint (str): API endpoint path

        Returns:
            JSON response data or None if no content
        """
        return http.delete(
            base_url=self.config.backend_url,
            endpoint=endpoint,
            token=self._token,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
        )

    def _call_fastapi_job_query(self):
        """Call FastAPI server job query functionality
        Maps to FastAPI Server's job_query.py module

        Returns:
            List of job status data dictionaries
        """
        return http.get(
            base_url=self.config.fastapi_url,
            endpoint="/fastapi/job/status",
            token=self._token,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
        )

    def start_job(self, qc_setup_list: list[str], service_name: str) -> JobResponse:
        """Start a new event job without reservation.

        Args:
            qc_setup_list (list[str]): List of QC setup names
            service_name (str): Name of the service to use

        Returns:
            JobResponse with job_id and status

        Raises:
            ValidationError: Invalid parameters
            JobCreationError: Job creation failed
            TimeoutError: Request timed out
        """
        # Validate parameters
        if not qc_setup_list or not all(qc_setup_list):
            raise ValidationError(
                "qc_setup_list cannot be empty and must not contain empty strings"
            )

        if not service_name or not service_name.strip():
            raise ValidationError("service_name cannot be empty")

        # Prepare request data
        data = {"qc_setup_list": qc_setup_list, "service_name": service_name.strip()}

        try:
            response_data = self._post("/api/jobs/", data=data)
            return JobResponse(**response_data)

        except QCTSSException as e:
            # Re-map specific errors for job creation context
            if e.http_status == 422:
                raise ValidationError(
                    f"Invalid job parameters: {e.backend_message}",
                    http_status=e.http_status,
                    error_code=e.error_code,
                    backend_message=e.backend_message,
                    details=e.details,
                ) from e
            elif e.http_status and 400 <= e.http_status < 500:
                raise JobCreationError(
                    f"Job creation failed: {e.backend_message}",
                    http_status=e.http_status,
                    error_code=e.error_code,
                    backend_message=e.backend_message,
                    details=e.details,
                ) from e

            raise e

    def get_my_jobs_status(self) -> list[JobStatus]:
        """Get status of all jobs for current user using
        FastAPI Server job query functionality.

        Returns:
            list of JobStatus objects

        Raises:
            AuthorizationError: Not authorized to access jobs
            TimeoutError: Request timed out
        """

        response_data = self._call_fastapi_job_query()
        return [JobStatus(**item) for item in response_data]

    def close_job(self, job_id: int) -> JobResponse:
        """Close a job (mark as completed).

        Args:
            job_id (int): Job ID to close

        Returns:
            JobResponse with updated status (completed)

        Raises:
            JobNotFoundError: Job not found
            InvalidJobStateError: Job cannot be closed in current state
            TimeoutError: Request timed out
            ValidationError: Invalid job_id
        """
        # Validate job_id
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValidationError(
                f"Invalid job_id: {job_id}. Must be positive integer."
            )

        try:
            response_data = self._post(f"/api/jobs/{job_id}/close/")
            result = JobResponse(**response_data)

            # Disconnect WebSocket now that job is closed
            if job_id in self._websocket_connections:
                self.unsubscribe_job_updates(job_id)

            return result

        except QCTSSException as e:
            # Re-map specific errors for job closing context
            if e.http_status == 409:  # Conflict - invalid state
                raise InvalidJobStateError(
                    f"Cannot close job {job_id}: {e.backend_message}",
                    http_status=e.http_status,
                    error_code=e.error_code,
                    backend_message=e.backend_message,
                    details=e.details,
                ) from e
            else:
                # Pass through other errors (404, 403, timeout, etc.)
                raise

    def cancel_job(self, job_id: int, reason: Optional[str] = None) -> JobResponse:
        """Cancel a job.

        Args:
            job_id (int): Job ID to cancel
            reason (Optional[str], optional): Optional reason for cancellation

        Returns:
            JobResponse with updated status (cancelled)

        Raises:
            JobNotFoundError: Job not found
            InvalidJobStateError: Job cannot be cancelled in current state
            TimeoutError: Request timed out
            ValidationError: Invalid job_id
        """
        # Validate job_id
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValidationError(
                f"Invalid job_id: {job_id}. Must be positive integer."
            )

        try:
            data = {"reason": reason or "User cancelled job"}
            response_data = self._post(f"/api/jobs/{job_id}/cancel/", data=data)
            result = JobResponse(**response_data)

            # Disconnect WebSocket now that job is cancelled
            if job_id in self._websocket_connections:
                self.unsubscribe_job_updates(job_id)

            return result

        except QCTSSException as e:
            # Re-map specific errors for job cancellation context
            if e.http_status == 409:  # Conflict - invalid state
                raise InvalidJobStateError(
                    f"Cannot cancel job {job_id}: {e.backend_message}",
                    http_status=e.http_status,
                    error_code=e.error_code,
                    backend_message=e.backend_message,
                    details=e.details,
                ) from e
                # Pass through other errors (404, 403, timeout, etc.)
            raise e

    def subscribe_job_updates(
        self,
        job_id: int,
        callback: Optional[Callable[[JobStatus], None]] = None,
        handle_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """Subscribe to real-time job status updates via WebSocket.

        Args:
            job_id (int): Job ID to monitor
            callback (Optional[Callable[[JobStatus], None]], optional):
                Optional function called with JobStatus updates
            handle_error (Optional[Callable[[Exception], None]], optional):
                Optional function called on WebSocket errors

        Raises:
            WebSocketError: Connection failed
            JobNotFoundError: Job not found
            ValidationError: Invalid job_id
        """
        # Validate job_id
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValidationError(
                f"Invalid job_id: {job_id}. Must be positive integer."
            )

        # Use WebSocket manager
        try:
            self._websocket_manager.connect(
                job_id=job_id,
                websocket_url=self.config.websocket_url,
                token=self._token,
                callback=callback,
                handle_error=handle_error,
            )

            # Track active connection
            self._websocket_connections[job_id] = True
            logger.info(f"Subscribed to job {job_id} updates")

        except Exception as e:
            logger.error(f"Failed to subscribe to job {job_id}: {e}")
            raise

    def unsubscribe_job_updates(self, job_id: int) -> None:
        """Unsubscribe from job updates.

        Args:
            job_id (int): Job ID to stop monitoring
        """
        if job_id in self._websocket_connections:
            self._websocket_manager.disconnect(job_id)
            del self._websocket_connections[job_id]
            logger.info(f"Unsubscribed from job {job_id} updates")

    def wait_until_running(
        self,
        job_id: int,
        timeout: int = MAX_TIMEOUT,
        on_status: Optional[Callable[[JobStatus], None]] = None,
        except_job_failed: bool = False,
    ) -> JobStatus:
        """Wait for job to transition from queued to running status.

        This method automatically:
        1. Subscribes to WebSocket updates
        2. Monitors status changes
        3. Returns when job reaches 'running' state
        4. Automatically disconnects WebSocket

        You can press Ctrl+C to cancel waiting and disconnect.

        Args:
            job_id (int): Job ID to monitor
            timeout (int):
                Maximum time to wait in seconds.
                Default is :const:`qctss_client.client.subscribe.MAX_TIMEOUT`
            on_status (Optional[Callable[[JobStatus], None]]):
                Optional callback for status updates during waiting
            except_job_failed (bool):
                Whether to raise an exception if caused by job failure.
                Default is False.

        Returns:
            JobStatus object when job reaches 'running' state.

        Raises:
            TimeoutError: If job doesn't reach 'running' state within timeout
            ValidationError: Invalid job_id
            WebSocketError: Connection failed
            KeyboardInterrupt: User pressed Ctrl+C

        Example:
            >>> job = client.start_job(qc_setup_list, service_name)
            >>> try:
            ...     port = client.wait_until_running(job.job_id, timeout=300)
            ...     print(f"get machine port: {port}")
            ...     # Continue with next steps
            ... except TimeoutError:
            ...     print("Job took too long to start")
            ... except KeyboardInterrupt:
            ...     print("Waiting cancelled by user (Ctrl+C)")
        """

        # Validate job_id
        validate_job_id(job_id)

        waiting_monitor = JobWaitingMonitor(
            job_id=job_id,
            unsubscribe_job_updates=self.unsubscribe_job_updates,
            timeout=timeout,
            on_status=on_status,
        )

        try:
            # Subscribe to job status updates
            self.subscribe_job_updates(
                job_id=job_id,
                callback=waiting_monitor.on_status_update,
                handle_error=waiting_monitor.on_error,
            )

            # Wait for job to reach running state (with timeout if specified)
            if not waiting_monitor.job_running_event.wait(timeout=timeout):
                # Timeout occurred
                self.unsubscribe_job_updates(job_id)
                raise TimeoutError(
                    f"Job {job_id} did not reach 'running' state within {timeout} seconds"
                )

            if isinstance(waiting_monitor.final_status, JobStatus):
                return waiting_monitor.final_status

            # Check if there was an error during waiting
            if waiting_monitor.exception_holder:
                if except_job_failed and isinstance(
                    waiting_monitor.exception_holder, JobFailedError
                ):
                    # Return None if job failed and except_job_failed is True
                    return JobStatus(
                        job_id=job_id,
                        status="failed",
                        error_message=str(waiting_monitor.exception_holder),
                    )
                # Re-raise the exception (could be JobFailedError or other)
                raise waiting_monitor.exception_holder

            raise RuntimeError(
                "Unexpected state while waiting for "
                + f"job {job_id}: {waiting_monitor.final_status}"
            )

        except KeyboardInterrupt:
            # User pressed Ctrl+C - clean up and re-raise
            print()
            print("-" * 50)
            print("Waiting cancelled by user (Ctrl+C)")
            logger.info(f"User cancelled waiting for job {job_id} (Ctrl+C)")
            raise KeyboardInterrupt(f"Waiting for job {job_id} cancelled by user")
        finally:
            # Ensure WebSocket is disconnected on exit
            self.unsubscribe_job_updates(job_id)

    def close(self) -> None:
        """Close all connections and clean up resources."""
        # Close all WebSocket connections
        self._websocket_manager.disconnect_all()
        self._websocket_connections.clear()
        logger.info("QC-Test Space Client closed")

    def download_qcsetup_config_file(
        self,
        paths: dict[str, Path],
    ) -> None:
        """
        批次下載多個 QCSetup 的 config 檔案並儲存至指定絕對路徑。

        Args:
            paths: {qcsetup_name: 絕對路徑} 對映表

        Raises:
            ValueError: 路徑非絕對路徑
            QCSetupNotActiveError: QCSetup 狀態非 active
            QCSetupConfigNotFoundError: QCSetup 無 activated config
            QCSetupNotFoundError: QCSetup 不存在
        """
        for name, output_path in paths.items():
            if not Path(output_path).is_absolute():
                raise ValueError(f"Path for '{name}' must be absolute: {output_path}")

        for name, output_path in paths.items():
            output_path = Path(output_path)

            url = (
                f"{self.config.backend_url}/api/"
                + f"qc-setups/by-name/{name}/download-config/"
            )
            headers = {"X-API-KEY": self._token}  # 使用 client token

            try:
                response = requests.get(
                    url, headers=headers, timeout=self.config.timeout
                )
            except requests.RequestException as e:
                raise Exception(f"Failed to connect to backend: {e}")

            if response.status_code == 403:
                raise QCSetupNotActiveError(f"QCSetup '{name}' is not active")
            elif response.status_code == 404:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = {}
                if error_body.get("error") == "No activated config found":
                    raise QCSetupConfigNotFoundError(
                        f"QCSetup '{name}' has no activated config"
                    )
                raise QCSetupNotFoundError(f"QCSetup '{name}' not found")
            elif response.status_code != 200:
                raise Exception(
                    "Failed to download config for "
                    + f"'{name}': {response.status_code} {response.text}"
                )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(response.text, encoding="utf-8")

    def download_qcsetup_wiring(
        self,
        paths: dict[str, Path],
    ) -> None:
        """
        批次下載多個 QCSetup 的 wiring 檔案並儲存至指定絕對路徑。

        Args:
            paths: {qcsetup_name: 絕對路徑} 對映表

        Raises:
            ValueError: 路徑非絕對路徑
            QCSetupNotActiveError: QCSetup 狀態非 active
            QCSetupNotFoundError: QCSetup 不存在
        """
        for name, output_path in paths.items():
            if not Path(output_path).is_absolute():
                raise ValueError(f"Path for '{name}' must be absolute: {output_path}")

        for name, output_path in paths.items():
            output_path = Path(output_path)

            url = (
                f"{self.config.backend_url}/api/"
                + f"qc-setups/by-name/{name}/download-wiring/"
            )
            headers = {"X-API-KEY": self._token}

            try:
                response = requests.get(
                    url, headers=headers, timeout=self.config.timeout
                )
            except requests.RequestException as e:
                raise QCTSSException(f"Failed to connect to backend: {e}")

            if response.status_code == 403:
                raise QCSetupNotActiveError(f"QCSetup '{name}' is not active")
            elif response.status_code == 404:
                raise QCSetupNotFoundError(f"QCSetup '{name}' not found")
            elif response.status_code != 200:
                raise QCTSSException(
                    "Failed to download wiring for "
                    + "'{name}': {response.status_code} {response.text}"
                )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(response.text, encoding="utf-8")
