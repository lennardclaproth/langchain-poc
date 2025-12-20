from fastmcp import Client
import pytest
import httpx
from asgi_lifespan import LifespanManager
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine


@pytest.fixture()
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture()
def app(test_engine):
    from app.main import create_app
    return create_app(engine=test_engine)

@pytest.fixture()
async def mcp_client(app):
    """
    In-process FastMCP client connected directly to your FastMCP server instance.
    Requires lifespan to have run so app.state.tool_engine exists.
    """
    mcp = app.state.tool_engine.mcp
    async with Client(mcp) as client:
        yield client
        
@pytest.fixture()
async def async_client(app):
    """
    Async HTTP client that:
    - runs FastAPI lifespan (startup/shutdown) so app.state.tool_engine is set
    - routes requests in-process via ASGITransport (no real network)
    """
    async with LifespanManager(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
