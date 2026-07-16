"""Validation utilities for QCTSS Client (:mod:`qctss_client.utils.validate`)"""

from ..exceptions import ValidationError


def validate_job_id(job_id: int) -> None:
    """Validate job ID parameter

    Args:
        job_id (int): Job ID to validate

    Raises:
        ValidationError: If job_id is invalid
    """

    if not isinstance(job_id, int) or job_id <= 0:
        raise ValidationError("Job ID must be a positive integer")


def validate_qc_setup_list(qc_setup_list: list[str]) -> None:
    """Validate QC setup list parameter

    Args:
        qc_setup_list (list[str]): QC setup list to validate

    Raises:
        ValidationError: If qc_setup_list is invalid
    """

    if not isinstance(qc_setup_list, list) or len(qc_setup_list) == 0:
        raise ValidationError("QC setup list cannot be empty")

    for item in qc_setup_list:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError("QC setup list items must be non-empty strings")


DATETIME_STR_FORMAT = "%Y-%m-%d %H:%M:%S"
"""Default datetime string format used for serialization and deserialization"""
