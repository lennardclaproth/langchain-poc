# app/api/schemas/tools.py
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID
import re

from pydantic import BaseModel, Field as PydanticField, ConfigDict, HttpUrl, model_validator, field_validator

from .spec_tools import ToolContract, ToolEndpoint, ToolResponseSpec

class CreateToolRequest(BaseModel):
    """
    Incoming payload for creating a tool.

    NOTE:
    - endpoint/contract/response are validated as *structured* models,
      then stored as dicts in Tool.endpoint/Tool.contract/Tool.response.
    - name must follow MCP tool naming standard (1-128 chars, only A-Z a-z 0-9 _ - .) as defined in https://modelcontextprotocol.io/specification/2025-11-25/server/tools
    """
    name: str
    description: str
    enabled: bool = True

    endpoint: Optional[ToolEndpoint] = None
    contract: Optional[ToolContract] = None
    response: Optional[ToolResponseSpec] = None

    @field_validator("name")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """Validates tool name follows MCP naming standard."""
        if not v or len(v) == 0:
            raise ValueError("Tool name cannot be empty")
        if len(v) > 128:
            raise ValueError("Tool name must be 128 characters or less")
        if not re.match(r"^[a-zA-Z0-9_\-.]+$", v):
            raise ValueError(
                "Tool name must only contain letters (A-Z, a-z), digits (0-9), "
                "underscore (_), hyphen (-), and dot (.)"
            )
        return v

    @model_validator(mode="after")
    def validate_payload(self):
        if not any([self.endpoint, self.contract, self.response]):
            raise ValueError("At least one of endpoint/contract/response must be provided.")
        return self

class UpdateToolRequest(BaseModel):
    """
    Partial update payload. Any field can be omitted.
    - name must follow MCP tool naming standard (1-128 chars, only A-Z a-z 0-9 _ - .) as defined in https://modelcontextprotocol.io/specification/2025-11-25/server/tools
    """
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None

    endpoint: Optional[ToolEndpoint] = None
    contract: Optional[ToolContract] = None
    response: Optional[ToolResponseSpec] = None

    @field_validator("name")
    @classmethod
    def validate_tool_name(cls, v: Optional[str]) -> Optional[str]:
        """Validates tool name follows MCP naming standard."""
        if v is None:
            return v
        if len(v) == 0:
            raise ValueError("Tool name cannot be empty")
        if len(v) > 128:
            raise ValueError("Tool name must be 128 characters or less")
        if not re.match(r"^[a-zA-Z0-9_\-.]+$", v):
            raise ValueError(
                "Tool name must only contain letters (A-Z, a-z), digits (0-9), "
                "underscore (_), hyphen (-), and dot (.)"
            )
        return v


class ToolResponse(BaseModel):
    """
    API response model.
    """
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    transport: Optional[str] = None

    endpoint: Optional[ToolEndpoint] = None
    contract: Optional[ToolContract] = None
    response: Optional[ToolResponseSpec] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None