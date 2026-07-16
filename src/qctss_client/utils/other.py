"""Other utility functions (:mod:`qctss_client.utils.other`)"""

import warnings
from importlib.metadata import version as pkg_version

from ..exceptions import InvalidPackageInfo

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

DATETIME_STR_FORMAT = "%Y-%m-%d %H:%M:%S"
"""Default datetime string format used for serialization and deserialization"""
