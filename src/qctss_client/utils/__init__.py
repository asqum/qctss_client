"""Utility functions (:mod:`qctss_client.utils`)"""

import warnings
from importlib.metadata import version as pkg_version

from ..exceptions import InvalidPackageInfo

from .validate import validate_job_id, validate_qc_setup_list, DATETIME_STR_FORMAT

SDK_NAME = "qctss-client"
"""SDK name for identification in requests"""


def get_sdk_version() -> str:
    """Get the SDK version for identification in requests"""
    try:
        return pkg_version(SDK_NAME)
    except (ImportError, ValueError) as e:
        warnings.warn(
            f"Could not retrieve SDK version. Due to {e}",
            InvalidPackageInfo,
        )
        return "unknown"


SDK_VERSION = get_sdk_version()
"""SDK version for identification in requests"""


__all__ = [
    "SDK_NAME",
    "SDK_VERSION",
    "DATETIME_STR_FORMAT",
    "validate_job_id",
    "validate_qc_setup_list",
]
