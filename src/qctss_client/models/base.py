"""Pydantic data model base class for QCTSS Client SDK. 
(`mod:`qctss_client.models.base`)"""

from typing import Any
from pydantic import BaseModel as PydanticBaseModel, ConfigDict


class BaseModel(PydanticBaseModel):
    """Local base model with friendlier notebook rendering."""

    model_config = ConfigDict(from_attributes=True)
    """Pydantic model configuration."""

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
