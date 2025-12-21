from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
from uuid import UUID

from app.internal.store.store_client import StoreClient, StoreClientNotFound, StoreClientForbidden, StoreClientError
from app.internal.agents.builder import AgentBuilder, RuntimeConfig
# from app.apm.client import client as elastic_client
import elasticapm
from elasticapm import capture_span

class AgentDisabled(Exception):
    pass


@dataclass(frozen=True)
class AgentRuntimeServiceConfig:
    agent_store_base_url: str
    mcp_url: str


class AgentRuntimeService:
    def __init__(self, cfg: AgentRuntimeServiceConfig):
        self.store = StoreClient(cfg.agent_store_base_url)
        self.builder = AgentBuilder(
            RuntimeConfig(
                agent_store_base_url=cfg.agent_store_base_url,
                mcp_url=cfg.mcp_url,
            ),
            store=self.store,
        )

    async def run(self, agent_id: UUID, message: str) -> Dict[str, Any]:
        elasticapm.label(agent_id=str(agent_id))
        elasticapm.set_custom_context({"msg_len": len(message)})

        try:
            with capture_span("store.get_agent", span_type="store", span_subtype="agent_store"):
                agent = await self.store.get_agent(agent_id)

        except StoreClientNotFound as e:
            raise ValueError(str(e))
        except StoreClientForbidden as e:
            raise PermissionError(str(e))
        except StoreClientError as e:
            raise RuntimeError(f"Store error: {e}")

        if not agent.enabled:
            raise AgentDisabled(f"Agent {agent_id} is disabled")

        with capture_span("builder.build", span_type="agent", span_subtype="builder"):
            runnable = await self.builder.build(agent)

        with capture_span("runnable.ainvoke", span_type="llm", span_subtype="invoke"):
            answer = await runnable.ainvoke(message)

        return {"agent_id": str(agent_id), "answer": answer}
