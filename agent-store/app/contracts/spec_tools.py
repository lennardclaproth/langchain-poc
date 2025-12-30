# app/api/schemas/tools.py
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, HttpUrl, field_validator, model_validator

JsonType = Literal["string", "integer", "number", "boolean", "object", "array"]

class JsonSchemaProperty(BaseModel):
    """
    JsonSchema property definition, it provides an interface with which
    we define the expected inputs and outputs of a tool.

    NOTE: For more information on the fields, see: https://json-schema.org/understanding-json-schema/
    2020-12 specification.
    """
    type: Optional[JsonType] = None
    description: Optional[str] = None
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None
    # Defines a constant field value, this can only be set in the code
    const: Optional[Any] = None
    # Static value for this property, useful for injecting fixed values via tool contracts.
    # This is not part of the JSON Schema spec and therefore prefixed with 'x_'
    x_static: Optional[Any] = None

    # simple constraints (extend anytime)
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None

    # nesting
    properties: Optional[Dict[str, "JsonSchemaProperty"]] = None
    items: Optional["JsonSchemaProperty"] = None

    @model_validator(mode="after")
    def validate_property(self):
        # min/max sanity
        if self.minLength is not None and self.minLength < 0:
            raise ValueError("minLength must be >= 0")
        if self.maxLength is not None and self.maxLength < 0:
            raise ValueError("maxLength must be >= 0")
        if self.minLength is not None and self.maxLength is not None and self.minLength > self.maxLength:
            raise ValueError("minLength cannot be > maxLength")

        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum cannot be > maximum")

        # type-driven structure constraints
        if self.type == "object":
            if self.items is not None:
                raise ValueError("object type cannot have 'items'")
        if self.type == "array":
            if self.properties is not None:
                raise ValueError("array type cannot have 'properties'")
            if self.items is None:
                raise ValueError("array type requires 'items'")

        # If properties/items are set, type should match (optional strictness)
        if self.properties is not None and self.type not in (None, "object"):
            raise ValueError("If 'properties' is set, type must be 'object'")
        if self.items is not None and self.type not in (None, "array"):
            raise ValueError("If 'items' is set, type must be 'array'")

        # enum sanity
        if self.enum is not None and len(self.enum) == 0:
            raise ValueError("enum cannot be an empty list")

        # const/type consistency
        if self.const is not None and self.type is not None:
            if not _is_instance_for_json_type(self.const, self.type):
                raise ValueError(f"const must match type '{self.type}'")

        return self

JsonSchemaProperty.model_rebuild()

def _is_instance_for_json_type(value: Any, t: JsonType) -> bool:
    if t == "string":
        return isinstance(value, str)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return (isinstance(value, (int, float)) and not isinstance(value, bool))
    if t == "boolean":
        return isinstance(value, bool)
    if t == "object":
        return isinstance(value, dict)
    if t == "array":
        return isinstance(value, list)
    return True


def _validate_value_against_property(value: Any, prop: JsonSchemaProperty, path: str) -> List[str]:
    """
    Returns a list of human-readable error strings.
    Conservative subset validation:
    - type
    - enum
    - minLength/maxLength for strings
    - minimum/maximum for numbers/integers
    - recursive validate for object/array if properties/items present
    """
    errs: List[str] = []

    if prop.type is not None and not _is_instance_for_json_type(value, prop.type):
        errs.append(f"{path}: expected {prop.type}, got {type(value).__name__}")
        return errs  # type mismatch: stop further checks

    if prop.enum is not None and value not in prop.enum:
        errs.append(f"{path}: value not in enum {prop.enum}")

    if isinstance(value, str):
        if prop.minLength is not None and len(value) < prop.minLength:
            errs.append(f"{path}: length < minLength ({prop.minLength})")
        if prop.maxLength is not None and len(value) > prop.maxLength:
            errs.append(f"{path}: length > maxLength ({prop.maxLength})")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if prop.minimum is not None and value < prop.minimum:
            errs.append(f"{path}: value < minimum ({prop.minimum})")
        if prop.maximum is not None and value > prop.maximum:
            errs.append(f"{path}: value > maximum ({prop.maximum})")

    # recurse for object
    if isinstance(value, dict) and prop.properties is not None:
        for k, subprop in prop.properties.items():
            if k in value:
                errs.extend(_validate_value_against_property(value[k], subprop, f"{path}.{k}"))

    # recurse for array
    if isinstance(value, list) and prop.items is not None:
        for idx, item in enumerate(value):
            errs.extend(_validate_value_against_property(item, prop.items, f"{path}[{idx}]"))
    
    # const check
    if prop.const is not None and value != prop.const:
        errs.append(f"{path}: must equal const {prop.const}")

    return errs

class ToolInputSchema(BaseModel):
    """
    The input schema for a tool contract. This is what is used by the LLM to
    understand what inputs to provide to the tool.
    """
    type: Literal["object"] = "object"
    # Properties is a dictionary mapping property names to their JsonSchemaProperty definitions
    properties: Dict[str, JsonSchemaProperty] = Field(default_factory=dict)
    # List of required property names
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
    Denotes how the tool's input schema maps to HTTP request components. i.e. which 
    input schema properties go into query params, JSON body, form data, or path params.
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
    input_schema: ToolInputSchema
    # The binding of the external http service. This is optional but required when 
    # the tool uses http transport. Denotes where the input schema is used.
    http: Optional[HttpBinding] = None
    tags: List[str] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    read_only: bool = False
    idempotent: bool = False
    cache_ttl_seconds: Optional[int] = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for t in v:
            if not isinstance(t, str):
                raise TypeError("tags must be strings")
            t2 = t.strip()
            if not t2:
                continue
            key = t2.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(t2)
        return out

    @field_validator("cache_ttl_seconds")
    @classmethod
    def validate_cache_ttl(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return None
        if not isinstance(v, int):
            raise TypeError("cache_ttl_seconds must be an integer")
        if v <= 0:
            raise ValueError("cache_ttl_seconds must be > 0")
        return v

    @model_validator(mode="after")
    def validate_planner_hints(self):
        if self.read_only and not self.idempotent:
            raise ValueError("read_only tools should be idempotent.")
        if self.cache_ttl_seconds is not None and not (self.read_only and self.idempotent):
            raise ValueError("cache_ttl_seconds requires read_only=True and idempotent=True.")
        return self

    @model_validator(mode="after")
    def validate_http_binding_keys_exist(self):
        """
        Ensure http binding references only keys present in the input schema.
        Also (optional) ensure all *path* params are required (common for URL templates).
        """
        if self.http is None:
            return self

        props = set(self.input_schema.properties.keys())
        for bucket_name, keys in {
            "query": self.http.query,
            "json": self.http.json,
            "form": self.http.form,
            "path": self.http.path,
        }.items():
            unknown = [k for k in keys if k not in props]
            if unknown:
                raise ValueError(f"http.{bucket_name} contains keys not in input_schema.properties: {unknown}")

        # Optional: path params should usually be required
        missing_required = [k for k in self.http.path if k not in self.input_schema.required]
        if missing_required:
            raise ValueError(f"http.path params should be required: {missing_required}")

        return self

    @model_validator(mode="after")
    def validate_examples_against_input_schema(self):
        schema = self.input_schema

        for i, ex in enumerate(self.examples):
            if not isinstance(ex, dict):
                raise TypeError(f"examples[{i}] must be an object/dict")

            # required keys present
            missing = [k for k in schema.required if k not in ex]
            if missing:
                raise ValueError(f"examples[{i}] missing required keys: {missing}")

            # unknown keys
            if schema.additionalProperties is False:
                unknown = [k for k in ex.keys() if k not in schema.properties]
                if unknown:
                    raise ValueError(
                        f"examples[{i}] contains unknown keys (additionalProperties=false): {unknown}"
                    )

            # validate known keys against properties
            errs: List[str] = []
            for k, v in ex.items():
                prop = schema.properties.get(k)
                if prop is None:
                    continue  # allowed only when additionalProperties=True
                errs.extend(_validate_value_against_property(v, prop, path=f"examples[{i}].{k}"))

            if errs:
                # avoid huge errors; show the first few
                preview = "; ".join(errs[:5])
                more = "" if len(errs) <= 5 else f" (+{len(errs) - 5} more)"
                raise ValueError(f"examples[{i}] failed schema validation: {preview}{more}")

        return self

class ToolResponseSpec(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    # The JSON schema defining the response structure
    json_schema: Dict[str, Any] = Field(default_factory=dict, alias="schema")
    # The format of the response, e.g. text, json, xml, etc.
    format: str = "text"

class ToolTransport(str, Enum):
    """
    The different transport mechanisms a tool can use.

    - http: standard HTTP calls
    - mcp: MCP protocol calls
    - internal: internal function calls
    """
    http = "http"
    mcp = "mcp"
    internal = "internal"

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

class ToolEndpoint(BaseModel):
    """
    The endpoint configuration for a tool.
    
    There are 3 different transport types supported: http, mcp, internal.

    NOTE: Depending on the transport, different fields are required.
    """
    # The transport the tool does, at the moment there are three supported transports
    transport: ToolTransport
    # http specific fields
    url: Optional[HttpUrl] = None
    method: Optional[HttpMethod] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    timeout: Optional[float] = None
    # mcp protocol specific fields
    mcp_server: Optional[str] = None
    mcp_tool: Optional[str] = None
    # internal tool specific fields
    target: Optional[str] = None # name of the internal tool to call
    static_inputs: Dict[str, Any] = Field(default_factory=dict) # static inputs to inject these map to values in the contract
    
    @model_validator(mode="after")
    def validate_transport_specific_fields(self):
        if self.transport == ToolTransport.http:
            if not self.url or not self.method:
                raise ValueError("For transport='http', 'url' and 'method' are required.")
            if self.mcp_server or self.mcp_tool:
                raise ValueError("For transport='http', MCP fields must be null.")
            return self
        
        if self.transport == ToolTransport.mcp:
            if not self.mcp_server or not self.mcp_tool:
                raise ValueError("For transport='mcp', 'mcp_server' and 'mcp_tool' are required.")
            if self.url or self.method:
                raise ValueError("For transport='mcp', HTTP fields must be null.")
            return self
        
        if self.transport == ToolTransport.internal:
            if not self.target:
                raise ValueError("For transport='internal', 'target' is required.")
            if self.url or self.method or self.mcp_server or self.mcp_tool:
                raise ValueError("For transport='internal', HTTP and MCP fields must be null.")
            return self

    @field_validator("method")
    @classmethod
    def normalize_method(cls, v):
        return v.upper() if isinstance(v, str) else v

    @field_validator("headers")
    @classmethod
    def validate_headers(cls, v: Dict[str, str]):
        for k in v.keys():
            if not k.strip():
                raise ValueError("Header names cannot be empty.")
        return v
