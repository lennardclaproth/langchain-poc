from __future__ import annotations

from typing import Any, Dict, Optional, Type
from uuid import UUID

import httpx
from pydantic import BaseModel, Field, create_model
from sqlmodel import Session, select

from app.internal.store import db
from app.internal.store.schema import Tool as ToolRow  # <-- adjust if your 

from app.contracts.spec_tools import ToolTransport  # <-- adjust import to your 


def _type_from_jsonschema(schema: Dict[str, Any]) -> Any:
    """
    Very small JSON-schema -> Python type mapper.
    Expands only the common primitives. Everything else becomes Any.
    """
    t = (schema or {}).get("type")

    if t == "string":
        return str
    if t == "integer":
        return int
    if t == "number":
        return float
    if t == "boolean":
        return bool
    if t == "object":
        return dict
    if t == "array":
        return list

    # If schema uses oneOf/anyOf/etc, keep it permissive
    return Any


def _pydantic_model_from_mcp_schema(tool_name: str, input_schema: Dict[str, Any]) -> Type[BaseModel]:
    """
    Builds a Pydantic model whose fields match the JSON schema object properties.
    This is how we get FastMCP to expose a matching MCP input schema, since it
    generates input schemas from function signatures. :contentReference[oaicite:1]{index=1}
    """
    if not input_schema:
        # No schema → accept empty object
        return create_model(f"{tool_name}Args")

    if input_schema.get("type") != "object":
        # MCP tools usually use object input. If yours don’t, accept Any.
        return create_model(f"{tool_name}Args", payload=(Any, Field(..., description="Tool input")))

    props = input_schema.get("properties") or {}
    required = set(input_schema.get("required") or [])

    fields: Dict[str, tuple[Any, Any]] = {}

    for key, prop_schema in props.items():
        py_type = _type_from_jsonschema(prop_schema)
        desc = (prop_schema or {}).get("description")

        if key in required:
            fields[key] = (py_type, Field(..., description=desc))
        else:
            fields[key] = (Optional[py_type], Field(None, description=desc))

    return create_model(f"{tool_name}Args", **fields)


async def _execute_http_tool(endpoint: dict, args: dict) -> Any:
    url = endpoint.get("url")
    method = (endpoint.get("method") or "POST").upper()
    headers = endpoint.get("headers") or {}

    if not url:
        raise ValueError("HTTP tool endpoint missing 'url'")

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.request(method, url, json=args, headers=headers)
        r.raise_for_status()

        ctype = r.headers.get("content-type", "")
        return r.json() if "application/json" in ctype else r.text


async def _execute_mcp_proxy_tool(endpoint: dict, args: dict) -> Any:
    """
    Proxy-call another MCP server/tool.
    """
    from fastmcp import Client

    server = endpoint.get("mcp_server")
    tool = endpoint.get("mcp_tool")

    if not server or not tool:
        raise ValueError("MCP tool endpoint missing 'mcp_server' or 'mcp_tool'")

    async with Client(server) as client:
        result = await client.call_tool(tool, args)
        return result.data


def _resolve_internal_target(target: str):
    """
    Resolve "package.module:function" to a callable.
    """
    import importlib

    if ":" not in target:
        raise ValueError("internal target must be in form 'package.module:function'")

    mod_name, fn_name = target.split(":", 1)
    mod = importlib.import_module(mod_name)
    fn = getattr(mod, fn_name, None)
    if fn is None:
        raise ValueError(f"Could not resolve internal target: {target}")
    return fn


async def _execute_internal_tool(endpoint: dict, args: dict) -> Any:
    target = endpoint.get("target")
    if not target:
        raise ValueError("Internal tool endpoint missing 'target'")

    fn = _resolve_internal_target(target)

    # support sync or async
    res = fn(**args)
    if hasattr(res, "__await__"):
        return await res
    return res


def register_db_tools(mcp) -> None:
    """
    Register all enabled Tool rows as FastMCP tools.

    Call this once during startup BEFORE serving MCP traffic.
    """
    with Session(db.engine) as session:
        tools = session.exec(select(ToolRow).where(ToolRow.enabled == True)).all()

    for row in tools:
        endpoint = row.endpoint or {}
        contract = row.contract or {}

        # Your ToolContract stores schema under alias "schema"
        # so DB likely contains {"schema": {...}}
        input_schema = contract.get("schema") or {}

        ArgsModel = _pydantic_model_from_mcp_schema(row.name, input_schema)

        # Factory to avoid the classic "loop variable late binding" bug.
        def make_impl(tool_id: UUID, endpoint_snapshot: dict):
            async def _impl(payload: ArgsModel) -> Any:
                args = payload.model_dump(mode="json")

                transport = endpoint_snapshot.get("transport")
                if transport == ToolTransport.http:
                    return await _execute_http_tool(endpoint_snapshot, args)
                if transport == ToolTransport.mcp:
                    return await _execute_mcp_proxy_tool(endpoint_snapshot, args)
                if transport == ToolTransport.internal:
                    return await _execute_internal_tool(endpoint_snapshot, args)

                raise ValueError(f"Unknown transport: {transport}")

            # nice name in stacktraces/logging
            _impl.__name__ = f"dbtool__{tool_id}"
            return _impl

        impl = make_impl(row.id, endpoint)

        # Register with FastMCP. Input schema comes from the ArgsModel signature. :contentReference[oaicite:2]{index=2}
        mcp.tool(
            name=row.name,
            description=row.description,
            enabled=row.enabled,
            meta={"tool_id": str(row.id)},
        )(impl)
