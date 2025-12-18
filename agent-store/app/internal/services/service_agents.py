from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlmodel import Session

from app.contracts.contract_agents import AgentCreate, AgentUpdate
from app.internal.store.schema import Agent
from app.internal.store.repository_agents import AgentRepository
from app.internal.store.repository_tools import ToolRepository

from .errors import ConflictError, NotFoundError, ValidationError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AgentService:
    def __init__(self, session: Session):
        self.repo = AgentRepository(session)
        self.tools = ToolRepository(session)

    def list_agents(self, *, enabled: Optional[bool] = None) -> Sequence[Agent]:
        return self.repo.list(enabled=enabled)

    def get_agent(self, agent_id: UUID) -> Agent:
        agent = self.repo.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(resource="Agent", identifier=str(agent_id))
        return agent

    def create_agent(self, payload: AgentCreate) -> Agent:
        if self.repo.get_by_name(payload.name):
            raise ConflictError(resource="Agent", field="name", value=payload.name)

        agent = Agent(
            name=payload.name,
            role=payload.role,
            instructions=payload.instructions,
            enabled=payload.enabled,
            created_at=utcnow(),
            updated_at=utcnow(),
        )

        if payload.model is not None:
            agent.set_model(payload.model)

        if payload.context_tool is not None:
            agent.set_context_tool(payload.context_tool)

        return self.repo.create(agent)

    def update_agent(self, agent_id: UUID, payload: AgentUpdate) -> Agent:
        agent = self.get_agent(agent_id)

        if payload.name and payload.name != agent.name:
            if self.repo.get_by_name(payload.name):
                raise ConflictError(resource="Agent", field="name", value=payload.name)
            agent.name = payload.name

        if payload.role is not None:
            agent.role = payload.role

        if payload.enabled is not None:
            agent.enabled = payload.enabled

        if payload.model is not None:
            agent.set_model(payload.model)

        if payload.context_tool is not None:
            agent.set_context_tool(payload.context_tool)

        agent.updated_at = utcnow()
        return self.repo.update(agent)

    def delete_agent(self, agent_id: UUID) -> None:
        agent = self.get_agent(agent_id)
        self.repo.delete_links_for_agent(agent_id)
        self.repo.delete(agent)

    def list_tools(self, agent_id: UUID):
        _ = self.get_agent(agent_id)
        return self.repo.list_tools(agent_id)

    def attach_tool(self, agent_id: UUID, tool_id: UUID) -> None:
        _ = self.get_agent(agent_id)
        tool = self.tools.get_by_id(tool_id)
        if not tool:
            raise NotFoundError(resource="Tool", identifier=str(tool_id))

        if self.repo.is_tool_linked(agent_id, tool_id):
            return

        self.repo.link_tool(agent_id, tool_id)

    def detach_tool(self, agent_id: UUID, tool_id: UUID) -> None:
        _ = self.get_agent(agent_id)
        self.repo.unlink_tool(agent_id, tool_id)
