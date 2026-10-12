"""Pydantic model for job management in QCTSS Client SDK.
(`mod:`qctss_client.models.job`)"""

from datetime import datetime
from typing import Optional, Any
from pydantic import Field, ConfigDict, model_validator

from .base import BaseModel


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
    job_id: int = Field(default=-1, description="Job ID")
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
            self.job_id = self.job.get("job_id", -1)
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
