"""Pydantic model for billing information in QCTSS Client SDK.
(`mod:`qctss_client.models.bill`)"""

from typing import Optional, Any
from pydantic import Field, ConfigDict

from .base import BaseModel


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
