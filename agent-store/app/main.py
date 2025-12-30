from contextlib import asynccontextmanager

from fastapi.responses import JSONResponse
import uvicorn
from fastapi import FastAPI, Request
from fastmcp import FastMCP

from .config.server_config import server_config
from .internal.store import db, db_vector

from .api.routers import tools, agents, chats, messages, vectors
from .internal.mcp.tool_compiler import ToolCompiler
from .internal.mcp.tool_engine import McpToolEngine

from .api.middleware.request_timing import RequestTimingMiddleware
from .api.middleware.global_exception_handler import GlobalExceptionHandler

from elasticapm.contrib.starlette import ElasticAPM 
from .apm.client import client as apm_client

from .logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger("app")

def build_mcp() -> FastMCP:
    mcp = FastMCP("agent-store")
    return mcp

def create_app(*, engine=None) -> FastAPI:
    """
    App factory. In tests, pass a SQLite in-memory engine.
    """
    logger.info("Setting up database engine.")
    if engine is not None:
        db.set_engine(engine)

    logger.info("Setting up MCP server")
    mcp = build_mcp()
    compiler = ToolCompiler()
    mcp_app = mcp.http_app(path="/mcp")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with mcp_app.lifespan(mcp_app):
            logger.info("Initializing databases")
            db.init_db()
            vector_client = db_vector.init_chroma()
            logger.info("Setting application state")
            app.state.tool_engine = McpToolEngine(mcp, compiler)
            app.state.mcp_app = mcp_app
            app.state.vector_client = vector_client
            logger.info("Syncing MCP Tools")
            await app.state.tool_engine.sync_all_enabled()
            yield

    app = FastAPI(title="agent-store", lifespan=lifespan)
    logger.info("Registering middlewares")
    
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(
        GlobalExceptionHandler,
        include_traceback=False,
        instance_base_url=None,
        error_header_name="X-Error-Id",
    )
    app.add_middleware(ElasticAPM, client=apm_client)
    logger.info("Registering routers")
    app.include_router(tools.router)
    app.include_router(agents.router)
    app.include_router(chats.router)
    app.include_router(messages.router)
    app.include_router(vectors.router)
    
    logger.info("Mounting MCP server")
    app.mount("/", mcp_app)
    return app

app = create_app()

def run():
    uvicorn.run(
        "app.main:app",
        host=server_config["host"],
        port=server_config["port"],
        reload=server_config.get("reload", False),
        access_log=False,
    )

if __name__ == "__main__":
    run()
