from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlmodel import Session, select, delete

from app.internal.store.schema import Agent, AgentToolLink, Tool


class AgentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, agent_id: UUID) -> Optional[Agent]:
        return self.session.get(Agent, agent_id)

    def get_by_name(self, name: str) -> Optional[Agent]:
        stmt = select(Agent).where(Agent.name == name)
        return self.session.exec(stmt).first()

    def list(self, *, enabled: Optional[bool] = None) -> Sequence[Agent]:
        stmt = select(Agent)
        if enabled is not None:
            stmt = stmt.where(Agent.enabled == enabled)
        return self.session.exec(stmt).all()

    def create(self, agent: Agent) -> Agent:
        self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
        return agent

    def update(self, agent: Agent) -> Agent:
        self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
        return agent

    def delete(self, agent: Agent) -> None:
        self.session.delete(agent)
        self.session.commit()

    # tool links
    def is_tool_linked(self, agent_id: UUID, tool_id: UUID) -> bool:
        stmt = select(AgentToolLink).where(
            AgentToolLink.agent_id == agent_id,
            AgentToolLink.tool_id == tool_id,
        )
        return self.session.exec(stmt).first() is not None

    def link_tool(self, agent_id: UUID, tool_id: UUID) -> None:
        self.session.add(AgentToolLink(agent_id=agent_id, tool_id=tool_id))
        self.session.commit()

    def unlink_tool(self, agent_id: UUID, tool_id: UUID) -> None:
        self.session.exec(
            delete(AgentToolLink).where(
                AgentToolLink.agent_id == agent_id,
                AgentToolLink.tool_id == tool_id,
            )
        )
        self.session.commit()

    def list_tools(self, agent_id: UUID) -> Sequence[Tool]:
        stmt = (
            select(Tool)
            .join(AgentToolLink, AgentToolLink.tool_id == Tool.id)
            .where(AgentToolLink.agent_id == agent_id)
        )
        return self.session.exec(stmt).all()

    def delete_links_for_agent(self, agent_id: UUID) -> None:
        self.session.exec(delete(AgentToolLink).where(AgentToolLink.agent_id == agent_id))
        self.session.commit()
