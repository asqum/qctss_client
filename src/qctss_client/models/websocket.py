"""Pydantic model for WebSocket messages in QCTSS Client SDK.
(`mod:`qctss_client.models.websocket`)"""

from datetime import datetime
from typing import Optional, Union
from pydantic import Field, ConfigDict

from .base import BaseModel
from .job import JobStatus


class WebSocketMessage(BaseModel):
    """WebSocket message format"""

    model_config = ConfigDict(from_attributes=True)

    type: str = Field(
        description="Message type (status_update, error, auth_required, etc.)"
    )
    job_id: Optional[int] = Field(
        default=None, description="Job ID for job-related messages"
    )
    status: Optional[str] = Field(default=None, description="Job status")
    queue_position: Optional[int] = Field(default=None, description="Queue position")
    port_number: Optional[int] = Field(default=None, description="Port number")
    progress: Optional[float] = Field(default=None, description="Job progress")
    estimated_completion: Optional[datetime] = Field(
        default=None, description="Estimated completion"
    )
    timestamp: Union[datetime, str] = Field(description="Message timestamp")
    error: Optional[str] = Field(default=None, description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")
    message: Optional[str] = Field(default=None, description="Human-readable message")

    def to_job_status(self) -> Optional[JobStatus]:
        """Convert to JobStatus if applicable"""
        if self.type not in {"status_update", "initial_status"}:
            return None

        if not self.job_id:
            return None

        return JobStatus(
            job_id=self.job_id,
            status=self.status or "unknown",
            queue_position=self.queue_position,
            port_number=self.port_number,
            progress=self.progress,
            estimated_completion=self.estimated_completion,
            created_at=(
                self.timestamp
                if isinstance(self.timestamp, datetime)
                else datetime.now()
            ),
            updated_at=(
                self.timestamp
                if isinstance(self.timestamp, datetime)
                else datetime.now()
            ),
        )


# Removed AuthMessage as of 2026-01-07 specification change
# WebSocket authentication now uses X-API-KEY header/token parameter 
# instead of message-based auth
