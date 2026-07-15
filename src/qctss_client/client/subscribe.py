"""QCTSS Client Subscribe Module (:mod:`qctss_client.client.subscribe`)

Handling of WebSocket subscriptions for job updates and
other real-time notifications from the QCTSS backend."""

from typing import Callable, Optional
import time
import logging
import threading
import sys

from ..models import JobStatus
from ..exceptions import JobFailedError
from ..utils import validate_job_id

logger = logging.getLogger(__name__)

MAX_TIMEOUT = 3600  # seconds

TERMINAL_STATES = {"cancelled", "failed", "timeout"}


class CLIJobMonitor:
    """Handles job monitoring in CLI mode with WebSocket updates.

    Args:
        job_id (int): Job ID to monitor
        timeout (int): Maximum time to wait for job completion (in seconds)
    """

    def __init__(
        self,
        job_id: int,
        timeout: int = MAX_TIMEOUT,
    ):
        validate_job_id(job_id)
        if timeout <= 0:
            raise ValueError("Timeout must be positive")

        self.job_id = job_id
        self.timeout = timeout
        self.stop_event = threading.Event()

        print(f"Monitoring job {self.job_id}... (Press Ctrl+C to stop)")

    def on_status_update(self, status: JobStatus):
        """Handle job status updates received from WebSocket.

        Args:
            status (JobStatus): The updated job status
        """
        print(
            f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] - "
            + f"[Job {self.job_id}] Status: {status.status}"
        )
        if status.queue_position:
            print(f"  Queue Position: {status.queue_position}")
        if status.status in TERMINAL_STATES:
            print(f"  Job finished with status: {status.status}")
            self.stop_event.set()

    def on_error(self, error: Exception):
        """Handle WebSocket errors during job monitoring.

        Args:
            error (Exception): The exception raised during WebSocket communication
        """
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] - " + f"[Job {self.job_id}]")
        print(f"  WebSocket error: {error}")
        print(f"\nWebSocket error: {error}", file=sys.stderr)
        self.stop_event.set()

    def wait(self):
        """Wait for job completion or timeout."""
        try:
            self.stop_event.wait(timeout=self.timeout)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")


class JobWaitingMonitor:
    """Handles waiting for job completion with WebSocket updates

    Args:
        job_id (int): Job ID to monitor
        unsubscribe_job_updates (Callable[[int], None]):
            Function to unsubscribe from job updates
        timeout (int):
            Maximum time to wait for job completion (in seconds)
        on_status (Optional[Callable[[JobStatus], None]]):
            Optional callback for status updates
    """

    def __init__(
        self,
        job_id: int,
        unsubscribe_job_updates: Callable[[int], None],
        timeout: int = MAX_TIMEOUT,
        on_status: Optional[Callable[[JobStatus], None]] = None,
    ):
        validate_job_id(job_id)
        if timeout <= 0:
            raise ValueError("Timeout must be positive")

        self.job_id = job_id
        self.unsubscribe_job_updates = unsubscribe_job_updates
        self.timeout = timeout
        self.on_status = on_status
        self.job_running_event = threading.Event()

        self.final_status: Optional[JobStatus] = None
        self.exception_holder: Optional[Exception] = None

    def _defer_disconnect(self):
        time.sleep(0.2)  # Wait for event.set() to propagate
        try:
            self.unsubscribe_job_updates(self.job_id)
        except Exception as e:
            print(f"Error during deferred disconnect for job {self.job_id}: {e}")

    def on_status_update(self, status: JobStatus):
        """Handle job status updates received from WebSocket.

        Args:
            status (JobStatus): The updated job status
        """
        print(f"\n[Job {self.job_id}] Status: {status.status}")
        if status.queue_position:
            print(f"  Queue Position: {status.queue_position}")
        if status.error_message:
            print(f"  Message: {status.error_message}")

        # Call user's callback if provided
        if self.on_status:
            self.on_status(status)

        logger.debug(f"[Job {self.job_id}] Status: {status.status}")
        time.sleep(0.2)

        self.final_status = status
        # Check if job has started running
        if status.status == "running":
            print(f"[Job {self.job_id}] NOW RUNNING!")
            self.job_running_event.set()  # Signal that job is running

            # Schedule WebSocket disconnect asynchronously to avoid blocking
            # (callback is running in WebSocket thread)

            threading.Thread(target=self._defer_disconnect, daemon=True).start()

        elif status.status in TERMINAL_STATES:
            print(f"[Job {self.job_id}] ENDED with status '{status.status}'")
            self.exception_holder = JobFailedError(
                f"Job {self.job_id} ended with status '{status.status}'"
            )
            self.job_running_event.set()  # Signal to exit waiting immediately

    def on_error(self, error: Exception):
        """Handle WebSocket errors during job monitoring.

        Args:
            error (Exception): The exception raised during WebSocket communication
        """
        print(f"\n[Job {self.job_id}] WebSocket error: {error}")
        self.exception_holder = error
        self.job_running_event.set()  # Signal to exit waiting immediately
