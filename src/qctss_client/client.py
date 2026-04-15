"""
QCTSS Client main class
"""
from typing import List, Optional, Callable, Any, Dict
import time
import logging
import json
import requests

from .config import BackendConfig
from .exceptions import (
    QCTSSException, 
    ValidationError, 
    QCSetupNotActiveError, 
    QCSetupNotFoundError
)
from .models import JobResponse, JobStatus
from .websocket_manager import WebSocketManager
from . import utils


logger = logging.getLogger(__name__)


class QCTSSClient:
    """
    Main client class for interacting with QCTSS backend
    """
    
    def __init__(
        self,
        token: str,
        backend_url: Optional[str] = None,
        fastapi_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
    ):
        """
        Initialize QCTSS Client
        
        Args:
            token: authentication token
            backend_url: Backend API URL (overrides config)
            fastapi_url: FastAPI server URL (overrides config)
            timeout: Request timeout in seconds (overrides config)
            max_retries: Max retry attempts (overrides config)
            retry_delay: Delay between retries in seconds (overrides config)
            
        Raises:
            ValidationError: If token is empty or None
        """
        if not token:
            raise ValidationError("Token cannot be empty")
        
        self.token = token
        self.config = BackendConfig(
            backend_url=backend_url,
            fastapi_url=fastapi_url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        self._websocket_connections: Dict[int, Any] = {}
        self._websocket_manager = WebSocketManager()
        
        logger.info(f"Initialized QCTSS Client for {self.config.backend_url}")
    
    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make GET request to backend API (Django)
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response data
        """
        return utils.get(
            base_url=self.config.backend_url,
            endpoint=endpoint,
            token=self.token,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            params=params,
        )
    
    def _get_fastapi(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make GET request to FastAPI server
        
        Args:
            endpoint: API endpoint path  
            params: Query parameters
            
        Returns:
            JSON response data
        """
        return utils.get(
            base_url=self.config.fastapi_url,
            endpoint=endpoint,
            token=self.token,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            params=params,
        )
    
    def _post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make POST request to backend API
        
        Args:
            endpoint: API endpoint path
            data: Request body data
            
        Returns:
            JSON response data
        """
        return utils.post(
            base_url=self.config.backend_url,
            endpoint=endpoint,
            token=self.token,
            data=data,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
        )
    
    def _put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make PUT request to backend API
        
        Args:
            endpoint: API endpoint path
            data: Request body data
            
        Returns:
            JSON response data
        """
        return utils.put(
            base_url=self.config.backend_url,
            endpoint=endpoint,
            token=self.token,
            data=data,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
        )
    
    def _delete(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Make DELETE request to backend API
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            JSON response data or None if no content
        """
        return utils.delete(
            base_url=self.config.backend_url,
            endpoint=endpoint,
            token=self.token,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
        )
    
    def start_job(self, qc_setup_list: List[str], service_name: str) -> JobResponse:
        """
        Start a new event job without reservation.
        
        Args:
            qc_setup_list: List of QC setup names
            service_name: Name of the service to use
            
        Returns:
            JobResponse with job_id and status
            
        Raises:
            ValidationError: Invalid parameters
            JobCreationError: Job creation failed
            TimeoutError: Request timed out
        """
        # Validate parameters
        if not qc_setup_list or not all(qc_setup_list):
            raise ValidationError("qc_setup_list cannot be empty and must not contain empty strings")
        
        if not service_name or not service_name.strip():
            raise ValidationError("service_name cannot be empty")
        
        # Prepare request data
        data = {
            "qc_setup_list": qc_setup_list,
            "service_name": service_name.strip()
        }
        
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
                    details=e.details
                ) from e
            elif e.http_status and 400 <= e.http_status < 500:
                from .exceptions import JobCreationError
                raise JobCreationError(
                    f"Job creation failed: {e.backend_message}",
                    http_status=e.http_status,
                    error_code=e.error_code,
                    backend_message=e.backend_message,
                    details=e.details
                ) from e
            else:
                # Pass through other errors (timeout, server errors)
                raise
    
    def get_my_jobs_status(self) -> list[JobStatus]:
        """
        Get status of all jobs for current user using FastAPI Server job query functionality
        

        Returns:
            list of JobStatus objects
            
        Raises:
            AuthorizationError: Not authorized to access jobs
            TimeoutError: Request timed out
        """
        
        try:
            # Call FastAPI server functionality through a dedicated endpoint
            # This maps to FastAPI Server's job_query.py module functionality
            response_data = self._call_fastapi_job_query()
            return [JobStatus(**item) for item in response_data]
        
        except QCTSSException as e:
            # Error mapping is already handled in utils.py, just pass through
            raise
    
    def _call_fastapi_job_query(self) -> list[Dict]:
        """
        Call FastAPI server job query functionality
        Maps to FastAPI Server's job_query.py module
        
        Returns:
            List of job status data dictionaries
        """
        return utils.get(
            base_url=self.config.fastapi_url.replace('ws://', 'http://').replace('wss://', 'https://'),
            endpoint="/fastapi/job/status",
            token=self.token,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
        )
    
    def close_job(self, job_id: int) -> JobResponse:
        """
        Close a job (mark as completed)
        
        Args:
            job_id: Job ID to close
            
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
            raise ValidationError(f"Invalid job_id: {job_id}. Must be positive integer.")
        
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
                from .exceptions import InvalidJobStateError
                raise InvalidJobStateError(
                    f"Cannot close job {job_id}: {e.backend_message}",
                    http_status=e.http_status,
                    error_code=e.error_code,
                    backend_message=e.backend_message,
                    details=e.details
                ) from e
            else:
                # Pass through other errors (404, 403, timeout, etc.)
                raise
    
    def cancel_job(self, job_id: int, reason: Optional[str] = None) -> JobResponse:
        """
        Cancel a job
        
        Args:
            job_id: Job ID to cancel
            reason: Optional reason for cancellation
            
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
            raise ValidationError(f"Invalid job_id: {job_id}. Must be positive integer.")
        
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
                from .exceptions import InvalidJobStateError
                raise InvalidJobStateError(
                    f"Cannot cancel job {job_id}: {e.backend_message}",
                    http_status=e.http_status,
                    error_code=e.error_code,
                    backend_message=e.backend_message,
                    details=e.details
                ) from e
            else:
                # Pass through other errors (404, 403, timeout, etc.)
                raise
    
    def subscribe_job_updates(
        self, 
        job_id: int, 
        callback: Optional[Callable[[JobStatus], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        """
        Subscribe to real-time job status updates via WebSocket
        
        Args:
            job_id: Job ID to monitor
            callback: Optional function called with JobStatus updates
            on_error: Optional error handler function
            
        Raises:
            WebSocketError: Connection failed
            JobNotFoundError: Job not found
            ValidationError: Invalid job_id
        """
        # Validate job_id
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValidationError(f"Invalid job_id: {job_id}. Must be positive integer.")
        
        # Default callback if none provided
        if callback is None:
            callback = lambda status: None
        
        # Use WebSocket manager
        try:
            self._websocket_manager.connect(
                job_id=job_id,
                websocket_url=self.config.websocket_url,
                token=self.token,
                callback=callback,
                on_error=on_error,
            )
            
            # Track active connection
            self._websocket_connections[job_id] = True
            logger.info(f"Subscribed to job {job_id} updates")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to job {job_id}: {e}")
            raise
    
    def unsubscribe_job_updates(self, job_id: int) -> None:
        """
        Unsubscribe from job updates
        
        Args:
            job_id: Job ID to stop monitoring
        """
        if job_id in self._websocket_connections:
            self._websocket_manager.disconnect(job_id)
            del self._websocket_connections[job_id]
            logger.info(f"Unsubscribed from job {job_id} updates")
    
    def wait_until_running(
        self, 
        job_id: int, 
        timeout: Optional[int] = None,
        on_status: Optional[Callable[[JobStatus], None]] = None
    ) -> int:
        """
        Wait for job to transition from queued to running status.
        
        This method automatically:
        1. Subscribes to WebSocket updates
        2. Monitors status changes
        3. Returns when job reaches 'running' state
        4. Automatically disconnects WebSocket
        
        You can press Ctrl+C to cancel waiting and disconnect.
        
        Args:
            job_id: Job ID to monitor
            timeout: Maximum time to wait in seconds (None = wait forever)
            on_status: Optional callback for status updates during waiting
            
        Returns:
            port_number: Port number assigned when job is running
            
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
        import threading
        
        # Validate job_id
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValidationError(f"Invalid job_id: {job_id}. Must be positive integer.")
        
        # Use threading event to signal when job is running
        job_running_event = threading.Event()
        final_status = None
        exception_holder = None
        
        def on_status_update(status: JobStatus):
            nonlocal final_status
            
            # Print status update
            print(f"\n[Job {job_id}] Status: {status.status}")
            if hasattr(status, 'queue_position') and status.queue_position is not None:
                print(f"  Queue Position: {status.queue_position}")
            if hasattr(status, 'message') and status.message:
                print(f"  Message: {status.message}")
            
            # Call user's callback if provided
            if on_status:
                on_status(status)
            
            logger.debug(f"Job {job_id} status: {status.status}")
            time.sleep(0.2)
            # Check if job has started running
            if status.status == "running":
                print(f"[Job {job_id}] NOW RUNNING!")
                port_number = status.port_number if hasattr(status, 'port_number') else None
                final_status = port_number
                job_running_event.set()  # Signal that job is running
                # Schedule WebSocket disconnect asynchronously to avoid blocking
                # (callback is running in WebSocket thread)
                def defer_disconnect():
                    
                    time.sleep(0.2)  # Wait for event.set() to propagate
                    try:
                        if job_id in self._websocket_connections:
                            self.unsubscribe_job_updates(job_id)
                    except Exception as e:
                        print(f"Error during deferred disconnect for job {job_id}: {e}")
                
                threading.Thread(target=defer_disconnect, daemon=True).start()
        
        def on_error(error: Exception):
            nonlocal exception_holder
            logger.error(f"WebSocket error for job {job_id}: {error}")
            exception_holder = error
            job_running_event.set()  # Signal to exit waiting
        
        try:
            # Subscribe to job status updates
            self.subscribe_job_updates(
                job_id=job_id,
                callback=on_status_update,
                on_error=on_error
            )
            
            # Wait for job to reach running state (with timeout if specified)
            if not job_running_event.wait(timeout=timeout):
                # Timeout occurred
                self.unsubscribe_job_updates(job_id)
                raise TimeoutError(
                    f"Job {job_id} did not reach 'running' state within {timeout} seconds"
                )
            
            # Check if there was an error during waiting
            if exception_holder:
                raise exception_holder
            
            # Return the final status
            if final_status:
                return final_status
            else:
                raise RuntimeError(f"Job {job_id} reached unknown state")
                
        except KeyboardInterrupt:
            # User pressed Ctrl+C - clean up and re-raise
            print(f"\n\nWaiting cancelled by user (Ctrl+C)")
            if job_id in self._websocket_connections:
                self.unsubscribe_job_updates(job_id)
            logger.info(f"User cancelled waiting for job {job_id} (Ctrl+C)")
            raise KeyboardInterrupt(f"Waiting for job {job_id} cancelled by user")
        except Exception as e:
            # Clean up on any other error
            if job_id in self._websocket_connections:
                self.unsubscribe_job_updates(job_id)
            raise
    
    def close(self) -> None:
        """
        Close all connections and clean up resources
        """
        # Close all WebSocket connections
        self._websocket_manager.disconnect_all()
        self._websocket_connections.clear()
        logger.info("RCCI Client closed")
    
    def download_qcsetup_config_file(
        self,
        qcsetup_names: List[str],
    ) -> Dict[str, dict]:
        """
        批次下載多個 QCSetup 的 config 檔案（in-memory）。

        Args:
            qcsetup_names: QCSetup name list

        Returns:
            Dict[str, dict] - key 為 qcsetup_name，value 為該 config 的 dict

        Raises:
            QCSetupNotActiveError: QCSetup 狀態非 active
            QCSetupNotFoundError: QCSetup 不存在
        """
        results = {}

        for name in qcsetup_names:
            url = f"{self.config.backend_url}/api/qc-setups/by-name/{name}/download-config/"
            headers = {"X-API-KEY": self.token}  # 使用 client token

            try:
                response = requests.get(url, headers=headers, timeout=self.config.timeout)
            except requests.RequestException as e:
                raise Exception(f"Failed to connect to backend: {e}")

            if response.status_code == 403:
                raise QCSetupNotActiveError(f"QCSetup '{name}' is not active")
            elif response.status_code == 404:
                raise QCSetupNotFoundError(f"QCSetup '{name}' not found")
            elif response.status_code != 200:
                raise Exception(f"Failed to download config for '{name}': {response.status_code} {response.text}")

            # 解析 JSON 並存入 dict
            try:
                results[name] = response.json()
            except json.JSONDecodeError as e:
                raise Exception(f"Invalid JSON response for '{name}': {e}")

        return results
    
    def download_qcsetup_wiring(
        self,
        qcsetup_names: List[str],
    ) -> Dict[str, dict]:
        """
        批次下載多個 QCSetup 的 wiring 檔案（in-memory）。

        Args:
            qcsetup_names: QCSetup name list

        Returns:
            Dict[str, dict] - key 為 qcsetup_name，value 為該 wiring 的 dict

        Raises:
            QCSetupNotActiveError: QCSetup 狀態非 active
            QCSetupNotFoundError: QCSetup 不存在
        """
        results = {}

        for name in qcsetup_names:
            url = f"{self.config.backend_url}/api/qc-setups/by-name/{name}/download-wiring/"
            headers = {"X-API-KEY": self.token}

            try:
                response = requests.get(url, headers=headers, timeout=self.config.timeout)
            except requests.RequestException as e:
                raise Exception(f"Failed to connect to backend: {e}")

            if response.status_code == 403:
                raise QCSetupNotActiveError(f"QCSetup '{name}' is not active")
            elif response.status_code == 404:
                raise QCSetupNotFoundError(f"QCSetup '{name}' not found")
            elif response.status_code != 200:
                raise Exception(f"Failed to download wiring for '{name}': {response.status_code} {response.text}")

            # 解析 JSON 並存入 dict
            try:
                results[name] = response.json()
            except json.JSONDecodeError as e:
                raise Exception(f"Invalid JSON response for '{name}': {e}")

        return results