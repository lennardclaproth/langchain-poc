# app/internal/mcp/tool_engine.py
from __future__ import annotations
import http
from typing import Any
from fastmcp import FastMCP
import httpx
from mcp import Tool
from sqlmodel import Session, select

from fastmcp.tools.tool import Tool

from app.internal.store import db
from app.internal.tools import registry
from app.internal.store.schema import Tool as DbTool
from app.contracts.spec_tools import ToolEndpoint, ToolTransport

from .tool_compiler import ToolCompiler

from app.logging_config import get_logger

logger = get_logger("app")

class McpToolEngine:
    """The mcp tool engine is responsible for managing and constructing
    elements that are needed for the MCP server to be as dynamic as possible.
    """
    def __init__(self, mcp:FastMCP, compiler: ToolCompiler):
        self.mcp = mcp
        self.compiler = compiler

    async def sync_all_enabled(self) -> None:
        """ Syncs all enabled tools.

        It requests all tools registered in the database and upserts them
        in the MCP server.
        """
        with Session(db.engine) as session:
            tools = session.exec(select(DbTool).where(DbTool.enabled == True)).all()
        for t in tools:
            logger.debug("Registering tool \"%s\"", t.name)
            await self.upsert(t)

    async def remove(self, tool: DbTool) -> None:
        """Removes the tools from the mcp server"""
        # Get available tools from the mcp server
        mcp_tools = await self.mcp.get_tools()
        # Try and get the tool based on its tool name
        mcp_tool = mcp_tools.get(tool.name)
        if mcp_tool == None:
            return
        # Remove the tool if it exists
        self.mcp.remove_tool(tool.name)

    async def upsert(self, tool: DbTool) -> None:
        """Upserts a tool
        
        - Compiles a function based off of the tool
        contract from the databse
        - Adds a name and a description
        - Generates a FastMCP interpretable function
        - Adds the tool to the MCP server

        Args:
            tool: the tool to be converted to an MCP server tool.
        """
        await self.remove(tool)
        # Return early if the tool is not enabled
        if not tool.enabled:
            return
        # Compile the function tool
        fn = self.compiler.compile_tool_fn(tool, dispatch=self._dispatch)
        fn.__name__ = tool.name
        fn.__doc__ = tool.description or ""
        # Calls the from_function helper of FastMCP to create a tool
        # from the compiled function
        mcp_tool = Tool.from_function(
            fn,
            name=tool.name,
            description=tool.description,
        )

        # Fallback if the mcp server does not have add_tool
        # The _tool_manager is supposed to be a private 
        # class according to python standards therefore we prefer
        # to not use it
        if hasattr(self.mcp, "add_tool"):
            self.mcp.add_tool(mcp_tool)
        else:
            self.mcp._tool_manager.add_tool(mcp_tool)

    async def _dispatch(self, tool: DbTool, args: dict[str, Any]) -> Any:
        """Dispatches the action based on the tool and it's config

        Args:
            tool: The tool to be executed, this is its config
            args: The arguments to call the tool with
        
        Returns:
            The result of the tool call.

        Raises:
            RuntimeError: If the transport type doesn't match the implemented transport types.
            HttpStatusError: If the http request does not have a status code success.
        """
        # Get the endpoint definition and transport type from the tool.
        try:
            endpoint: ToolEndpoint = tool.get_endpoint()
            transport: ToolTransport = endpoint.transport
        except Exception as e:
            raise RuntimeError(f"Failed to parse tool endpoint for tool {tool.name}: {str(e)}") from e

        # If the transport is http, build a http request and send the
        # request, wait for the response and return the response.
        if transport == ToolTransport.http:
            method = endpoint.method
            url = endpoint.url
            headers = endpoint.headers
            timeout = endpoint.timeout or 10.0

            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == http.HTTPMethod.GET:
                    r = await client.request(method, url, params=args, headers=headers)
                else:
                    r = await client.request(method, url, json=args, headers=headers)
                r.raise_for_status()
                return await r.json() if "application/json" in (r.headers.get("content-type") or "") else r.text
        # If the transport type is internal, look up the internal tool in the registry
        # and call its function with the provided arguments.
        if transport == ToolTransport.internal:
            # Get the internal tool key from the endpoint definition
            internal_key = endpoint.target
            if not internal_key:
                raise RuntimeError("Internal tool missing 'target' in endpoint definition.")
            # Look up in registry
            internal_tool_def = registry.get_internal_tool(internal_key)
            if not internal_tool_def:
                raise RuntimeError(f"Unknown internal tool: {internal_key}")
            # Call tool with unpacked arguments
            args = {**args, **(endpoint.static_inputs or {})}
            return await internal_tool_def.fn(**args)

        raise RuntimeError(f"Unsupported transport: {transport}")
