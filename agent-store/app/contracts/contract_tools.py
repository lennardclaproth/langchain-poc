# app/api/schemas/tools.py
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field as PydanticField, ConfigDict, HttpUrl, model_validator

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

    endpoint: Optional[ToolEndpoint] = None
    contract: Optional[ToolContract] = None
    response: Optional[ToolResponseSpec] = None

    @model_validator(mode="after")
    def validate_payload(self):
        if not any([self.endpoint, self.contract, self.response]):
            raise ValueError("At least one of endpoint/contract/response must be provided.")
        return self

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

    endpoint: Optional[ToolEndpoint] = None
    contract: Optional[ToolContract] = None
    response: Optional[ToolResponseSpec] = None

    created_at: datetime
    updated_at: datetime
