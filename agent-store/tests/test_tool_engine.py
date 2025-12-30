"""Unit tests for McpToolEngine._dispatch function."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlmodel import Session

from app.internal.mcp.tool_engine import McpToolEngine
from app.internal.store.schema import Tool as DbTool
from app.contracts.spec_tools import ToolEndpoint, ToolTransport, ToolContract, ToolInputSchema, ToolResponseSpec
from app.internal.tools.registry import InternalToolDef

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_mcp():
    """Mock FastMCP instance."""
    return MagicMock()


@pytest.fixture
def mock_compiler():
    """Mock ToolCompiler instance."""
    return MagicMock()


@pytest.fixture
def tool_engine(mock_mcp, mock_compiler):
    """Create a McpToolEngine instance with mocked dependencies."""
    return McpToolEngine(mcp=mock_mcp, compiler=mock_compiler)


def create_db_tool(
    name: str = "test_tool",
    transport: ToolTransport = ToolTransport.http,
    url: str = "https://api.example.com/test",
    method: str = "POST",
    target: str = None,
    static_inputs: dict = None,
) -> DbTool:
    """Helper to create a DbTool instance."""
    endpoint_dict = {
        "transport": transport.value if isinstance(transport, ToolTransport) else transport,
        "url": url if transport == ToolTransport.http else None,
        "method": method if transport == ToolTransport.http else None,
        "headers": {},
        "timeout": 10.0,
        "target": target if transport == ToolTransport.internal else None,
        "static_inputs": static_inputs if static_inputs is not None else {},
    }
    
    tool = DbTool(
        name=name,
        description="Test tool",
        enabled=True,
        endpoint=endpoint_dict,
        contract={},
        response={},
    )
    return tool


class TestDispatchHttpTransport:
    """Tests for HTTP transport dispatch."""

    async def test_dispatch_http_post_with_json_response(self, tool_engine):
        """Test HTTP POST request returns JSON response."""
        tool = create_db_tool(transport=ToolTransport.http, method="POST")
        args = {"query": "test", "limit": 5}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json = AsyncMock(return_value={"result": "success"})
            mock_response.headers = {"content-type": "application/json"}
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await tool_engine._dispatch(tool, args)

            assert result == {"result": "success"}
            mock_client.request.assert_called_once()
            call_args = mock_client.request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[1]["json"] == args

    async def test_dispatch_http_get_with_params(self, tool_engine):
        """Test HTTP GET request passes arguments as query parameters."""
        tool = create_db_tool(transport=ToolTransport.http, method="GET")
        args = {"query": "test", "limit": 5}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.text = "success"
            mock_response.headers = {"content-type": "text/plain"}
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await tool_engine._dispatch(tool, args)

            assert result == "success"
            mock_client.request.assert_called_once()
            call_args = mock_client.request.call_args
            assert call_args[0][0] == "GET"
            assert call_args[1]["params"] == args

    async def test_dispatch_http_text_response(self, tool_engine):
        """Test HTTP request with text/plain response."""
        tool = create_db_tool(transport=ToolTransport.http, method="GET")
        args = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.text = "plain text response"
            mock_response.headers = {"content-type": "text/plain"}
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await tool_engine._dispatch(tool, args)

            assert result == "plain text response"

    async def test_dispatch_http_request_failure(self, tool_engine):
        """Test HTTP request that raises an error."""
        tool = create_db_tool(transport=ToolTransport.http, method="POST")
        args = {"query": "test"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock(side_effect=Exception("HTTP 500"))
            
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(Exception, match="HTTP 500"):
                await tool_engine._dispatch(tool, args)


class TestDispatchInternalTransport:
    """Tests for internal transport dispatch."""

    async def test_dispatch_internal_tool_success(self, tool_engine):
        """Test dispatching to an internal tool successfully."""
        tool = create_db_tool(
            transport=ToolTransport.internal,
            target="test.tool",
            static_inputs={"prefix": "[DEBUG]"}
        )
        args = {"message": "hello"}

        # Mock the internal tool function
        mock_tool_fn = AsyncMock(return_value={"status": "ok"})
        mock_tool_def = InternalToolDef(
            key="test.tool",
            contract=ToolContract(input_schema=ToolInputSchema()),
            response=ToolResponseSpec(schema={}),
            fn=mock_tool_fn,
        )

        with patch("app.internal.mcp.tool_engine.registry.get_internal_tool", return_value=mock_tool_def):
            result = await tool_engine._dispatch(tool, args)

            assert result == {"status": "ok"}
            # Verify the tool was called with merged args and static_inputs as keyword arguments
            mock_tool_fn.assert_called_once_with(message="hello", prefix="[DEBUG]")

    async def test_dispatch_internal_tool_static_inputs_override(self, tool_engine):
        """Test that static inputs override args."""
        tool = create_db_tool(
            transport=ToolTransport.internal,
            target="test.tool",
            static_inputs={"key": "static_value"}
        )
        args = {"key": "arg_value", "other": "data"}

        mock_tool_fn = AsyncMock(return_value={})
        mock_tool_def = InternalToolDef(
            key="test.tool",
            contract=ToolContract(input_schema=ToolInputSchema()),
            response=ToolResponseSpec(schema={}),
            fn=mock_tool_fn,
        )

        with patch("app.internal.mcp.tool_engine.registry.get_internal_tool", return_value=mock_tool_def):
            await tool_engine._dispatch(tool, args)

            # Static inputs should override args - verified as keyword arguments
            mock_tool_fn.assert_called_once_with(key="static_value", other="data")

    async def test_dispatch_internal_tool_no_static_inputs(self, tool_engine):
        """Test internal tool dispatch with None static_inputs."""
        tool = create_db_tool(
            transport=ToolTransport.internal,
            target="test.tool",
            static_inputs=None
        )
        args = {"message": "test"}

        mock_tool_fn = AsyncMock(return_value={})
        mock_tool_def = InternalToolDef(
            key="test.tool",
            contract=ToolContract(input_schema=ToolInputSchema()),
            response=ToolResponseSpec(schema={}),
            fn=mock_tool_fn,
        )

        with patch("app.internal.mcp.tool_engine.registry.get_internal_tool", return_value=mock_tool_def):
            await tool_engine._dispatch(tool, args)

            # Verify called with keyword arguments
            mock_tool_fn.assert_called_once_with(message="test")

    async def test_dispatch_internal_tool_argument_mapping(self, tool_engine):
        """Test that arguments are correctly merged with static_inputs before passing to internal tool."""
        # Test 1: Args only, no static_inputs
        tool = create_db_tool(
            transport=ToolTransport.internal,
            target="test.tool",
            static_inputs={}
        )
        args = {"param1": "value1", "param2": "value2"}

        mock_tool_fn = AsyncMock(return_value={"status": "ok"})
        mock_tool_def = InternalToolDef(
            key="test.tool",
            contract=ToolContract(input_schema=ToolInputSchema()),
            response=ToolResponseSpec(schema={}),
            fn=mock_tool_fn,
        )

        with patch("app.internal.mcp.tool_engine.registry.get_internal_tool", return_value=mock_tool_def):
            await tool_engine._dispatch(tool, args)
            
            # Verify the tool was called with exactly the args as keyword arguments
            mock_tool_fn.assert_called_once_with(param1="value1", param2="value2")

    async def test_dispatch_internal_tool_argument_mapping_with_static(self, tool_engine):
        """Test that static_inputs are properly merged and override matching args."""
        tool = create_db_tool(
            transport=ToolTransport.internal,
            target="test.tool",
            static_inputs={"api_key": "secret123", "override_param": "static_value"}
        )
        args = {"query": "search_term", "override_param": "arg_value", "limit": 10}

        mock_tool_fn = AsyncMock(return_value={"status": "ok"})
        mock_tool_def = InternalToolDef(
            key="test.tool",
            contract=ToolContract(input_schema=ToolInputSchema()),
            response=ToolResponseSpec(schema={}),
            fn=mock_tool_fn,
        )

        with patch("app.internal.mcp.tool_engine.registry.get_internal_tool", return_value=mock_tool_def):
            await tool_engine._dispatch(tool, args)
            
            # Verify the tool was called with merged args where static_inputs take precedence
            mock_tool_fn.assert_called_once_with(
                query="search_term",
                limit=10,
                api_key="secret123",
                override_param="static_value",  # static value overrides arg
            )

    async def test_dispatch_internal_tool_missing_target(self, tool_engine):
        """Test error when internal tool missing target."""
        tool = create_db_tool(
            transport=ToolTransport.internal,
            target=None
        )
        args = {}

        with pytest.raises(RuntimeError, match=""):
            await tool_engine._dispatch(tool, args)

    async def test_dispatch_internal_tool_not_found(self, tool_engine):
        """Test error when internal tool not registered."""
        tool = create_db_tool(
            transport=ToolTransport.internal,
            target="unknown.tool"
        )
        args = {}

        with patch("app.internal.mcp.tool_engine.registry.get_internal_tool", return_value=None):
            with pytest.raises(RuntimeError, match="Unknown internal tool"):
                await tool_engine._dispatch(tool, args)


class TestDispatchUnsupportedTransport:
    """Tests for unsupported transport types."""

    async def test_dispatch_unsupported_transport(self, tool_engine):
        """Test error for unsupported transport type."""
        # Create a tool with MCP transport (which is defined but not implemented in _dispatch)
        tool = create_db_tool(transport=ToolTransport.http)
        # Set a valid transport but then manually create an endpoint with mcp_server/mcp_tool to bypass validation
        tool.endpoint = {
            "transport": "mcp",
            "mcp_server": "some_server",
            "mcp_tool": "some_tool",
            "url": None,
            "method": None,
            "headers": {},
            "target": None,
            "static_inputs": {},
        }
        args = {}

        with pytest.raises(RuntimeError, match="Unsupported transport"):
            await tool_engine._dispatch(tool, args)
