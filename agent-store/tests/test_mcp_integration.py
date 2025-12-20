import pytest

from sqlmodel import Session, select
from app.internal.store import db
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


async def test_call_tool_returns_expected_result(
    app,
    async_client,
    mcp_client,
    monkeypatch,
):
    """
    Docstring for test_call_tool_returns_expected_result
    
    :param app: The FastAPI application
    :type app: FastAPI
    :param async_client: An async client with the lifespan of the FastAPI app
    :type async_client: AsyncClient
    :param mcp_client: A client for the FastMCP server hosted by FastAPI
    :type mcp_client: Client
    :param monkeypatch: To mock and overwrite functions
    :type monkeypatch: MonkeyPatch

    This function tests that an MCP tool is callable.
    """
    # ARRANGE

    # We setup a fake function here to prevent the actual dispatch
    # function to start making http calls externally.
    async def fake_dispatch(tool, args):
        return {
            "tool": tool.name,
            "received": args,
            "status": "ok",
        }
    monkeypatch.setattr(app.state.tool_engine, "_dispatch", fake_dispatch)

    res = await async_client.post("/tools", json=valid_payload("callable_tool"))
    assert res.status_code == 201, res.text

    # ACT
    result = await mcp_client.call_tool(
        name="callable_tool",
        arguments={
            "q": "hello",
            "limit": 2,
        },
    )

    # ASSERT
    assert result.data == {
        "tool": "callable_tool",
        "received": {
            "q": "hello",
            "limit": 2,
        },
        "status": "ok",
    }