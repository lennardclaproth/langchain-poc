import uuid
from fastapi import FastAPI
from fastmcp import FastMCP
import pytest
import httpx
from sqlmodel import Session, select

from app.internal.store import db
from app.internal.mcp.tool_engine import McpToolEngine
from app.internal.store.schema import Tool as DbTool

pytestmark = pytest.mark.asyncio


def valid_payload(name: str = "my_tool") -> dict:
    return {
        "name": name,
        "description": "Test tool",
        "enabled": True,
        "endpoint": {
            "transport": "http",
            "url": "https://example.com/api/tools",
            "method": "POST",
            "headers": {"x-test": "1"},
        },
        "contract": {
            "schema_version": "jsonschema-2020-12",
            "input_schema": {
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Query", "minLength": 1},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3},
                },
                "required": ["q"],
                "additionalProperties": False,
            },
            "http": {"json": ["q", "limit"], "query": [], "form": [], "path": []},
            "tags": ["Search", "search", "Tools"],
            "examples": [{"q": "hello", "limit": 3}, {"q": "world"}],
            "read_only": False,
            "idempotent": False,
        },
        "response": {
            "schema": {"type": "object", "properties": {"result": {"type": "string"}}, "required": ["result"]},
            "format": "json",
        },
    }


async def test_create_tool(app, async_client, mcp_client):
    """
    Docstring for test_create_tool_creates_db_and_mcp
    
    :param app: The FastAPI application
    :type app: FastAPI
    :param async_client: An async client with the lifespan of the FastAPI app
    :type async_client: AsyncClient
    :param mcp_client: A client for the FastMCP server hosted by FastAPI
    :type mcp_client: Client

    This test checks if a tool gets properly created, persisted and also immediately
    listed on the MCP server.
    """
    # ARRANGE
    payload = valid_payload("tool_db_create")

    # ACT
    res = await async_client.post("/tools", json=payload)
    assert res.status_code == 201, res.text

    # ASSERT

    # Assert changes persisted in the database
    with Session(db.engine) as s:
        tool = s.exec(select(DbTool).where(DbTool.name == "tool_db_create")).first()
        assert tool is not None
        assert tool.description == payload["description"]
        assert tool.enabled is True

    # Assert MCP server has tool in runtime
    tools = await app.state.tool_engine.mcp.get_tools()
    mcp_tool = tools.get("tool_db_create")
    assert mcp_tool is not None

    # Assert MCP server lists tool
    listed = await mcp_client.list_tools()
    t = next((t for t in listed if t.name == "tool_db_create"), None)
    assert t is not None

async def test_validation_requires_one_of_endpoint_contract_response(app, async_client):
    res = await async_client.post(
        "/tools",
        json={"name": "invalid", "description": "x", "enabled": True},
    )
    assert res.status_code == 422, res.text

async def test_update_tool(app, async_client, mcp_client):
    """
    Docstring for test_update_tool
    
    :param app: The FastAPI application
    :type app: FastAPI
    :param async_client: An async client with the lifespan of the FastAPI app
    :type async_client: AsyncClient
    :param mcp_client: A client for the FastMCP server hosted by FastAPI
    :type mcp_client: Client

    This test checks if updating a tool gets correctly persisted in the database
    and that these changes also get properly reflected on the MCP server.
    """
    # ARRANGE
    create_res = await async_client.post("/tools", json=valid_payload("mcp_tool_update_1"))
    assert create_res.status_code == 201, create_res.text
    created = create_res.json()
    tool_id = uuid.UUID(created["id"])

    tools_before = await app.state.tool_engine.mcp.get_tools()
    assert tools_before.get("mcp_tool_update_1") is not None

    listed_before = await mcp_client.list_tools()
    assert any(t.name == "mcp_tool_update_1" for t in listed_before)

    # ACT
    patch_payload = {"description": "UPDATED DESCRIPTION"}
    update_res = await async_client.patch(f"/tools/{tool_id}", json=patch_payload)
    assert update_res.status_code in (200, 204), update_res.text

    # ASSERT

    # Assert database changes are persisted
    with Session(db.engine) as s:
        db_tool = s.exec(select(DbTool).where(DbTool.id == tool_id)).first()
        assert db_tool is not None
        assert db_tool.description == "UPDATED DESCRIPTION"

    # Assert MCP runtime updated
    tools_after = await app.state.tool_engine.mcp.get_tools()
    mcp_tool = tools_after.get("mcp_tool_update_1")
    assert mcp_tool is not None

    # Try common description locations
    desc = getattr(mcp_tool, "description", None)
    if desc is None:
        desc = getattr(getattr(mcp_tool, "meta", None), "description", None)
    if desc is None:
        fn = getattr(mcp_tool, "fn", None) or getattr(mcp_tool, "function", None)
        desc = (getattr(fn, "__doc__", None) or None)

    assert desc == "UPDATED DESCRIPTION"

    # Assert FastMCP client view updated too
    listed_after = await mcp_client.list_tools()
    tool = next((t for t in listed_after if t.name == "mcp_tool_update_1"), None)
    assert tool is not None
    assert tool.description == "UPDATED DESCRIPTION"