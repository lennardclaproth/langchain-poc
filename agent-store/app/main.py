from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI
from fastmcp import FastMCP
import httpx
import uvicorn
from .config.server_config import server_config
from .internal.store import db
from .api.routers import tools, agents, chats, messages
from .internal.mcp.tool_compiler import ToolCompiler

mcp = FastMCP("agent-store")
compiler = ToolCompiler()

@mcp.tool()
async def get_weather(location: Annotated[str, "The location of the item"]) -> str:
    """Get current weather for a location (via Open-Meteo, no API key)."""
    async with httpx.AsyncClient(timeout=10) as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1, "language": "en", "format": "json"},
        )
        geo.raise_for_status()
        geo_json = geo.json()
        if not geo_json.get("results"):
            return f"Could not find coordinates for '{location}'."

        r = geo_json["results"][0]
        lat, lon = r["latitude"], r["longitude"]
        name = r.get("name", location)
        country = r.get("country", "")

        wx = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": True},
        )
        wx.raise_for_status()
        cur = wx.json().get("current_weather")
        if not cur:
            return f"Weather data unavailable for {name}."

        return (
            f"Current weather in {name}{', ' + country if country else ''}: "
            f"{cur.get('temperature')}°C, wind {cur.get('windspeed')} km/h, "
            f"weathercode {cur.get('weathercode')}."
        )

mcp_app = mcp.http_app(path='/mcp')

from app.internal.mcp.tool_engine import McpToolEngine

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp_app.lifespan(mcp_app):
        db.init_db()
        app.state.tool_engine = McpToolEngine(mcp, compiler)
        await app.state.tool_engine.sync_all_enabled()
        yield

app = FastAPI(title="agent-store", lifespan=lifespan)
app.include_router(tools.router)
app.include_router(agents.router)
app.include_router(chats.router)
app.include_router(messages.router)
app.mount("/", mcp_app)

def run():
    uvicorn.run(
        "app.main:app",
        host=server_config["host"],
        port=server_config["port"],
        reload=server_config.get("reload", False),
    )

if __name__ == "__main__":
    run()
