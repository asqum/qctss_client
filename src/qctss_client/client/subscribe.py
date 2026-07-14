"""QCTSS Client Subscribe Module (:mod:`qctss_client.client.subscribe`)

Handling of WebSocket subscriptions for job updates and
other real-time notifications from the QCTSS backend."""

from typing import Callable, Optional
import time
import logging
import threading

from ..models import JobStatus
from ..exceptions import JobFailedError
from ..utils import validate_job_id

logger = logging.getLogger(__name__)

MAX_TIMEOUT = 3600  # seconds

TERMINAL_STATES = {"cancelled", "failed", "timeout"}


class JobWaitingMonitor:
    """Handles waiting for job completion with WebSocket updates"""

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
        print(f"\n[Job {self.job_id}] Status: {status.status}")
        if (status_queue := getattr(status, "queue_position", None)) is not None:
            print(f"  Queue Position: {status_queue}")
        if (status_msg := getattr(status, "message", None)) is not None:
            print(f"  Message: {status_msg}")

        # Call user's callback if provided
        if self.on_status:
            self.on_status(status)

        logger.debug(f"Job {self.job_id} status: {status.status}")
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
        print(f"\n[Job {self.job_id}] WebSocket error: {error}")
        self.exception_holder = error
        self.job_running_event.set()  # Signal to exit waiting immediately
