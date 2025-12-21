from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID
import httpx
import elasticapm
from elasticapm import capture_span

class StoreClientError(Exception):
    pass


class StoreClientNotFound(StoreClientError):
    pass


class StoreClientForbidden(StoreClientError):
    pass


@dataclass(frozen=True)
class ToolDTO:
    id: UUID
    name: str


@dataclass(frozen=True)
class AgentDTO:
    id: UUID
    name: str
    role: str
    enabled: bool
    model: Dict[str, Any]
    context_tool: Optional[Dict[str, Any]]
    # tools may or may not be included in the /agents/{id} response
    tools: Optional[List[ToolDTO]] = None


def _tool_from_json(obj: Dict[str, Any]) -> ToolDTO:
    if "id" not in obj or "name" not in obj:
        raise StoreClientError(f"Tool payload missing id/name: {obj}")
    return ToolDTO(id=UUID(str(obj["id"])), name=str(obj["name"]))


def _agent_from_json(obj: Dict[str, Any]) -> AgentDTO:
    missing = [k for k in ("id", "name", "role", "enabled", "model") if k not in obj]
    if missing:
        raise StoreClientError(f"Agent payload missing fields {missing}: {obj}")

    tools = None
    if isinstance(obj.get("tools"), list):
        tools = [_tool_from_json(t) for t in obj["tools"]]

    return AgentDTO(
        id=UUID(str(obj["id"])),
        name=str(obj["name"]),
        role=str(obj["role"]),
        enabled=bool(obj["enabled"]),
        model=dict(obj.get("model") or {}),
        context_tool=obj.get("context_tool"),
        tools=tools,
    )


class StoreClient:
    """
    Thin HTTP client for the agent-store API.
    Keep this boring and predictable: no LangChain, no MCP, no FastAPI here.
    """

    def __init__(self, base_url: str, timeout_s: float = 15.0):
        self.base_url = base_url
        self.timeout_s = timeout_s
        self._client = httpx.AsyncClient(timeout=timeout_s)

    async def aclose(self):
        await self._client.aclose()

    async def get_agent(self, agent_id: UUID) -> AgentDTO:
        url = f"{self.base_url}/agents/{agent_id}"
        r = await self._client.get(url)
        if r.status_code == 404:
            raise StoreClientNotFound(f"Agent {agent_id} not found")
        if r.status_code == 403:
            raise StoreClientForbidden(f"Agent {agent_id} forbidden")
        r.raise_for_status()
        data = r.json()
        return _agent_from_json(data)
    
    async def list_agent_tools(self, agent_id: UUID) -> List[ToolDTO]:
        url = f"{self.base_url}/agents/{agent_id}/tools"
        r = await self._client.get(url)

        if r.status_code == 404:
            raise StoreClientNotFound(f"Agent {agent_id} not found (tools)")
        r.raise_for_status()

        data = r.json()
        if not isinstance(data, list):
            raise StoreClientError(f"Expected list of tools, got: {type(data)}")
        return [_tool_from_json(t) for t in data]
