"""
Pydantic data models for RCCI Client SDK
"""

from datetime import datetime
from typing import Optional, Any, Union
from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict, model_validator


class BaseModel(PydanticBaseModel):
    """Local base model with friendlier notebook rendering."""

    model_config = ConfigDict(from_attributes=True)

    def _repr_pretty_(self, p: Any, cycle: bool) -> None:
        """Render a compact multiline representation in IPython/Jupyter."""
        if cycle:
            p.text(f"{self.__class__.__name__}(...)")
            return

        fields = self.model_dump(exclude_none=True)
        p.begin_group(2, f"{self.__class__.__name__}(")
        for index, (name, value) in enumerate(fields.items()):
            if index:
                p.text(",")
                p.breakable()
            p.text(f"{name}=")
            p.pretty(value)
        p.end_group(2, ")")


class JobResponse(BaseModel):
    """Response from job creation/update operations

    Supports two formats:
    1. Legacy format: {job_id: int, status: str, message: str}
    2. New API format: {message: str, job: {job_id: int, status: str, ...}, ...}
    """

    model_config = ConfigDict(from_attributes=True)

    # Core fields that are always present
    message: str = Field(description="Response message")

    # Support both legacy and new format
    job_id: Optional[int] = Field(default=None, description="Job ID")
    status: Optional[str] = Field(default=None, description="Job status")

    # New API format support - optional nested structure
    job: Optional[dict[str, Any]] = Field(
        default=None, description="Job details (new format)"
    )
    job_threads: list[dict[str, Any]] = Field(
        default_factory=list, description="Job threads created"
    )
    total_requested_setups: Optional[int] = Field(
        default=None, description="Total requested QC setups"
    )
    total_created_threads: Optional[int] = Field(
        default=None, description="Total created threads"
    )
    service_name: Optional[str] = Field(default=None, description="Service name")
    token_info: Optional[dict[str, Any]] = Field(
        default=None, description="Token information"
    )
    thread_errors: Optional[list[dict[str, Any]]] = Field(
        default=None, description="Thread creation errors"
    )

    @model_validator(mode="after")
    def extract_nested_format(self) -> "JobResponse":
        """Extract job_id and status from nested job dict if not present at top level"""
        # pylint: disable=no-member
        if self.job_id is None and isinstance(self.job, dict):
            self.job_id = self.job.get("job_id")
        if self.status is None and isinstance(self.job, dict):
            self.status = self.job.get("status")
        # pylint: enable=no-member
        return self

    def get_job_id(self) -> int:
        """Get job_id - returns 0 if not found (deprecated, use .job_id directly)"""
        return self.job_id or 0

    def get_status(self) -> str:
        """Get status - returns 'unknown' if not found (deprecated, use .status directly)"""
        return self.status or "unknown"


class JobStatus(BaseModel):
    """Detailed job status information"""

    model_config = ConfigDict(from_attributes=True)

    job_id: int = Field(description="Unique job identifier")
    status: str = Field(
        description="Current job status (queued, running, completed, failed, cancelled)"
    )
    user_id: Optional[int] = Field(
        default=None, description="User ID who created the job"
    )
    queue_position: Optional[int] = Field(
        default=None, description="Position in queue (for queued jobs)"
    )
    port_number: Optional[int] = Field(
        default=None, description="Assigned port number (for running jobs)"
    )
    progress: Optional[float] = Field(
        default=None, ge=0.0, le=100.0, description="Job progress percentage"
    )
    estimated_completion: Optional[datetime] = Field(
        default=None, description="Estimated completion time"
    )
    created_at: Optional[datetime] = Field(
        default=None, description="Job creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )
    job_start: Optional[datetime] = Field(
        default=None, description="Job start timestamp"
    )
    timeout_at: Optional[datetime] = Field(
        default=None, description="Job timeout timestamp"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Job start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Job completion timestamp"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if job failed"
    )
    service_name: Optional[str] = Field(
        default=None, description="Service used for this job"
    )
    qc_setup_list: Optional[list[str]] = Field(
        default=None, description="QC setups used"
    )

    @property
    def is_terminal(self) -> bool:
        """Check if job is in terminal state"""
        return self.status in {"completed", "failed", "cancelled", "timeout"}

    @property
    def is_active(self) -> bool:
        """Check if job is actively running"""
        return self.status in {"queued", "running"}


class BillingData(BaseModel):
    """Billing information data"""

    model_config = ConfigDict(from_attributes=True)

    year: int = Field(ge=2000, le=3000, description="Billing year")
    month: int = Field(ge=1, le=12, description="Billing month")
    user_id: int = Field(description="User identifier")
    user_name: str = Field(description="User name")
    total_usage: float = Field(ge=0.0, description="Total usage amount")
    total_cost: float = Field(ge=0.0, description="Total cost")
    currency: str = Field(default="USD", description="Currency code")
    details: Optional[dict[str, Any]] = Field(
        default=None, description="Additional billing details"
    )


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
# WebSocket authentication now uses X-API-KEY header/token parameter instead of message-based auth
