# app/api/schemas/tools.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field as PydanticField, ConfigDict, HttpUrl

from .spec_tools import ToolContract, ToolEndpoint, ToolResponseSpec

class ToolCreate(BaseModel):
    """
    Incoming payload for creating a tool.

    NOTE:
    - endpoint/contract/response are validated as *structured* models,
      then stored as dicts in Tool.endpoint/Tool.contract/Tool.response.
    """
    name: str
    description: str
    enabled: bool = True

    endpoint: ToolEndpoint
    contract: ToolContract = PydanticField(default_factory=ToolContract)
    response: ToolResponseSpec = PydanticField(default_factory=ToolResponseSpec)


class ToolUpdate(BaseModel):
    """
    Partial update payload. Any field can be omitted.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None

    endpoint: Optional[ToolEndpoint] = None
    contract: Optional[ToolContract] = None
    response: Optional[ToolResponseSpec] = None


class ToolRead(BaseModel):
    """
    API response model.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    enabled: bool

    endpoint: Dict[str, Any]
    contract: Dict[str, Any]
    response: Dict[str, Any]

    created_at: datetime
    updated_at: datetime
