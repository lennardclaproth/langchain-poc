# app/api/schemas/tools.py
from __future__ import annotations

from typing import Any, Dict, Optional

from enum import Enum

from pydantic import BaseModel, Field as PydanticField, ConfigDict, HttpUrl

class ToolContract(BaseModel):
    # Avoid shadowing BaseModel.schema(); keep wire key as "schema"
    model_config = ConfigDict(populate_by_name=True)
    json_schema: Dict[str, Any] = PydanticField(default_factory=dict, alias="schema")


class ToolResponseSpec(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    json_schema: Dict[str, Any] = PydanticField(default_factory=dict, alias="schema")
    format: str = "text"

class ToolTransport(str, Enum):
    http = "http"
    mcp = "mcp"
    internal = "internal"

class ToolEndpoint(BaseModel):
    transport: ToolTransport

    url: Optional[HttpUrl] = None
    method: Optional[str] = None
    headers: Dict[str, str] = PydanticField(default_factory=dict)

    mcp_server: Optional[str] = None
    mcp_tool: Optional[str] = None

    target: Optional[str] = None


