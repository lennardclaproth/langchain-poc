# app/internal/mcp/tool_subscriber.py
from __future__ import annotations
import keyword
import re
from typing import Any, Literal
from fastmcp import FastMCP
import httpx
from mcp import Tool
from pydantic import BaseModel, Field, create_model
from sqlmodel import Session, select

from fastmcp.tools.tool import Tool, ToolResult
from fastmcp.tools.tool_manager import ToolManager

from app.internal.store import db
from app.internal.store.schema import Tool as DbTool, ToolTransport

class McpToolSubscriber:
    def __init__(self, mcp:FastMCP):
        self.mcp = mcp
        # keep track if you want, but name-based removal is usually enough

    _JSON_TO_PY = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "object": "dict",
        "array": "list",
    }

    def _safe_ident(sefl, name: str) -> str:
        name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        if not name or name[0].isdigit() or keyword.iskeyword(name):
            name = f"p_{name}"
        return name

    def _build_flat_fn(self, tool: DbTool):
        contract = tool.contract or {}
        input_schema = contract.get("input_schema") or {}
        props = input_schema.get("properties", {}) or {}
        required = set(input_schema.get("required", []) or [])

        # Map JSON names -> safe python identifiers
        name_map: dict[str, str] = {raw: self._safe_ident(raw) for raw in props.keys()}

        # Build function signature
        sig_parts: list[str] = []
        for raw, spec in props.items():
            py_name = name_map[raw]
            py_type = self._JSON_TO_PY.get(spec.get("type"), "Any")

            if raw in required:
                sig_parts.append(f"{py_name}: {py_type}")
            else:
                default_expr = repr(spec.get("default", None))
                sig_parts.append(f"{py_name}: {py_type} | None = {default_expr}")

        signature = ", ".join(sig_parts)

        # Build body: pack args back into dict using original (raw) keys
        lines = [f"async def _impl({signature}, _t=tool):", "    args = {}"]
        for raw, py_name in name_map.items():
            lines.append(f"    if {py_name} is not None:")
            lines.append(f"        args[{raw!r}] = {py_name}")
        lines.append("    return await self._dispatch(_t, args)")
        src = "\n".join(lines)

        ns: dict[str, Any] = {"tool": tool, "self": self, "Any": Any}
        exec(src, ns)
        fn = ns["_impl"]
        return fn

    async def sync_all_enabled(self) -> None:
        with Session(db.engine) as session:
            tools = session.exec(select(DbTool).where(DbTool.enabled == True)).all()
        for t in tools:
            await self.upsert(t)

    async def remove(self, tool: DbTool) -> None:
        # remove from MCP regardless of enabled
        if not getattr(self.mcp, "_tool_manager", None): return
        mcp_tools = await self.mcp.get_tools()
        mcp_tool = mcp_tools.get(tool.name)
        if mcp_tool == None:
            return
        self.mcp.remove_tool(tool.name)

    async def upsert(self, tool: DbTool) -> None:
        await self.remove(tool)

        if not tool.enabled:
            return

        flat_fn = self._build_flat_fn(tool)
        flat_fn.__name__ = tool.name
        flat_fn.__doc__ = tool.description or ""

        mcp_tool = Tool.from_function(
            flat_fn,
            name=tool.name,
            description=tool.description,
        )

        # Prefer public API if your version has it
        if hasattr(self.mcp, "add_tool"):
            self.mcp.add_tool(mcp_tool)
        else:
            self.mcp._tool_manager.add_tool(mcp_tool)

    def _build_params_model(self, tool: DbTool) -> type[BaseModel]:
        contract = tool.contract or {}

        # New shape (recommended)
        input_schema = contract.get("input_schema")
        props = input_schema.get("properties", {}) or {}
        required = set(input_schema.get("required", []) or [])

        fields: dict[str, tuple[Any, Any]] = {}
        for name, spec in props.items():
            t = spec.get("type")
            py_t = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
                "object": dict,
                "array": list,
            }.get(t, Any)

            enum_vals = spec.get("enum")
            if enum_vals:
                py_t = Literal[tuple(enum_vals)]

            if name in required:
                default = ...
                ann = py_t
            else:
                default = spec.get("default", None)
                ann = py_t | None

            fields[name] = (ann, Field(default, description=spec.get("description")))

        safe_name = tool.name.title().replace("-", "").replace("_", "")
        return create_model(f"{safe_name}Params", **fields)  # type: ignore[arg-type]

    async def _dispatch(self, tool: DbTool, args: dict[str, Any]) -> Any:
        ep = tool.endpoint or {}
        transport = ep.get("transport")

        if transport == ToolTransport.http:
            method = (ep.get("method") or "POST").upper()
            url = ep["url"]
            headers = ep.get("headers") or {}
            timeout = ep.get("timeout", 15)

            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "GET":
                    r = await client.request(method, url, params=args, headers=headers)
                else:
                    r = await client.request(method, url, json=args, headers=headers)
                r.raise_for_status()
                return r.json() if "application/json" in (r.headers.get("content-type") or "") else r.text

        # TODO: ToolTransport.mcp / internal
        raise RuntimeError(f"Unsupported transport: {transport}")
