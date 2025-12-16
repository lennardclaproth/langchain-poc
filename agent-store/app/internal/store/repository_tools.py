# app/repositories/tools.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from .schema import Tool, ToolEndpoint, ToolContract, ToolResponseSpec


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ToolRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, tool_id: UUID) -> Optional[Tool]:
        return self.session.get(Tool, tool_id)

    def get_by_name(self, name: str) -> Optional[Tool]:
        stmt = select(Tool).where(Tool.name == name)
        return self.session.exec(stmt).first()

    def create(
        self,
        *,
        name: str,
        description: str,
        enabled: bool,
        endpoint: ToolEndpoint,
        contract: ToolContract,
        response: ToolResponseSpec,
    ) -> Tool:
        tool = Tool(
            name=name,
            description=description,
            enabled=enabled,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        tool.set_endpoint(endpoint)
        tool.set_contract(contract)
        tool.set_response(response)

        self.session.add(tool)
        self.session.commit()
        self.session.refresh(tool)
        return tool

    def update(
        self,
        tool: Tool,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        enabled: Optional[bool] = None,
        endpoint: Optional[ToolEndpoint] = None,
        contract: Optional[ToolContract] = None,
        response: Optional[ToolResponseSpec] = None,
    ) -> Tool:
        if name is not None:
            tool.name = name
        if description is not None:
            tool.description = description
        if enabled is not None:
            tool.enabled = enabled
        if endpoint is not None:
            tool.set_endpoint(endpoint)
        if contract is not None:
            tool.set_contract(contract)
        if response is not None:
            tool.set_response(response)

        tool.updated_at = utcnow()

        self.session.add(tool)
        self.session.commit()
        self.session.refresh(tool)
        return tool

    def delete(self, tool: Tool) -> None:
        self.session.delete(tool)
        self.session.commit()
