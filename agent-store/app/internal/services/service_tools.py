# app/services/tools.py
from __future__ import annotations

from uuid import UUID

from sqlmodel import Session

from app.contracts.contract_tools import ToolCreate, ToolUpdate
from app.internal.store.schema import Tool, ToolTransport
from app.internal.store.repository_tools import ToolRepository

from .errors import ConflictError, NotFoundError, ValidationError

class ToolService:
    def __init__(self, session: Session):
        self.repo = ToolRepository(session)

    def _validate_endpoint(self, endpoint) -> None:
        if endpoint.transport == ToolTransport.http:
            if endpoint.url is None or not endpoint.method:
                raise ValidationError("HTTP transport requires endpoint.url and endpoint.method")

        elif endpoint.transport == ToolTransport.mcp:
            if not endpoint.mcp_server or not endpoint.mcp_tool:
                raise ValidationError("MCP transport requires endpoint.mcp_server and endpoint.mcp_tool")

        elif endpoint.transport == ToolTransport.internal:
            if not endpoint.target:
                raise ValidationError("Internal transport requires endpoint.target")

        else:
            # defensive: if ToolTransport expands, you'll notice here
            raise ValidationError(f"Unknown transport '{endpoint.transport}'")

    def create_tool(self, payload: ToolCreate) -> Tool:
        existing = self.repo.get_by_name(payload.name)
        if existing:
            raise ConflictError(resource="Tool", field="name", value=payload.name)

        self._validate_endpoint(payload.endpoint)

        return self.repo.create(
            name=payload.name,
            description=payload.description,
            enabled=payload.enabled,
            endpoint=payload.endpoint,
            contract=payload.contract,
            response=payload.response,
        )

    def get_tool(self, tool_id: UUID) -> Tool:
        tool = self.repo.get_by_id(tool_id)
        if not tool:
            raise NotFoundError(resource="Tool", identifier=str(tool_id))
        return tool

    def update_tool(self, tool_id: UUID, payload: ToolUpdate) -> Tool:
        tool = self.get_tool(tool_id)

        if payload.name and payload.name != tool.name:
            if self.repo.get_by_name(payload.name):
                raise ConflictError(resource="Tool", field="name", value=payload.name)

        if payload.endpoint is not None:
            self._validate_endpoint(payload.endpoint)

        return self.repo.update(
            tool,
            name=payload.name,
            description=payload.description,
            enabled=payload.enabled,
            endpoint=payload.endpoint,
            contract=payload.contract,
            response=payload.response,
        )

    def delete_tool(self, tool_id: UUID) -> None:
        tool = self.get_tool(tool_id)
        self.repo.delete(tool)
