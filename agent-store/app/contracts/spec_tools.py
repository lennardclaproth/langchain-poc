# app/api/schemas/tools.py
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, HttpUrl, model_validator

JsonType = Literal["string", "integer", "number", "boolean", "object", "array"]

class JsonSchemaProperty(BaseModel):
    type: Optional[JsonType] = None
    description: Optional[str] = None
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None

    # simple constraints (extend anytime)
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None

    # nesting
    properties: Optional[Dict[str, "JsonSchemaProperty"]] = None
    items: Optional["JsonSchemaProperty"] = None

JsonSchemaProperty.model_rebuild()


class ToolInputSchema(BaseModel):
    type: Literal["object"] = "object"
    properties: Dict[str, JsonSchemaProperty] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)
    additionalProperties: bool = False

    @model_validator(mode="after")
    def required_must_exist(self):
        missing = [k for k in self.required if k not in self.properties]
        if missing:
            raise ValueError(f"required contains keys not in properties: {missing}")
        return self


class HttpBinding(BaseModel):
    """
    Optional: explicit mapping of inputs -> HTTP request parts.
    If omitted, your dispatcher can default: GET->query, others->json.
    """
    query: List[str] = Field(default_factory=list)
    json: List[str] = Field(default_factory=list)
    form: List[str] = Field(default_factory=list)
    path: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def no_overlap(self):
        seen: Dict[str, str] = {}
        for bucket, items in {
            "query": self.query, "json": self.json, "form": self.form, "path": self.path
        }.items():
            for k in items:
                if k in seen:
                    raise ValueError(f"Param '{k}' appears in both '{seen[k]}' and '{bucket}'")
                seen[k] = bucket
        return self

class ToolContract(BaseModel):
    schema_version: Literal["jsonschema-2020-12", "jsonschema-draft-07"] = "jsonschema-2020-12"

    # canonical input schema for the tool
    input_schema: ToolInputSchema

    # optional HTTP mapping rules (only used for transport=http)
    http: Optional[HttpBinding] = None

    # metadata
    tags: List[str] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)

    # planner hints
    read_only: bool = False
    idempotent: bool = False
    cache_ttl_seconds: Optional[int] = None

class ToolResponseSpec(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    json_schema: Dict[str, Any] = Field(default_factory=dict, alias="schema")
    format: str = "text"

class ToolTransport(str, Enum):
    http = "http"
    mcp = "mcp"
    internal = "internal"

class ToolEndpoint(BaseModel):
    transport: ToolTransport

    url: Optional[HttpUrl] = None
    method: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)

    mcp_server: Optional[str] = None
    mcp_tool: Optional[str] = None

    target: Optional[str] = None


