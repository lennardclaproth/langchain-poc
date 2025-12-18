# app/services/service_tools.py
from __future__ import annotations

from uuid import UUID

from sqlmodel import Sequence, Session

from app.contracts.contract_tools import ToolCreate, ToolUpdate
from app.internal.store.schema import Tool, ToolTransport
from app.internal.store.repository_tools import ToolRepository

from .errors import ConflictError, NotFoundError, ValidationError
from .ports import ToolSyncPort

class ToolService:
    def __init__(self, session: Session, sync: ToolSyncPort | None = None):
        self.repo = ToolRepository(session)
        self.sync = sync


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

        tool = self.repo.create(
            name=payload.name,
            description=payload.description,
            enabled=payload.enabled,
            endpoint=payload.endpoint,
            contract=payload.contract,
            response=payload.response,
        )

        # Ensure DB write succeeded before syncing (repo.create should commit/flush)
        if self.sync:
            self.sync.upsert(tool)

        return tool

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

        tool = self.repo.update(
            tool,
            name=payload.name,
            description=payload.description,
            enabled=payload.enabled,
            endpoint=payload.endpoint,
            contract=payload.contract,
            response=payload.response,
        )

        if self.sync:
            # if renamed, simplest is: remove old name then upsert new
            self.sync.upsert(tool)

        return tool

    def get_all_tools(self) -> Sequence[Tool]:
        return self.repo.get_all()

    def delete_tool(self, tool_id: UUID) -> None:
        tool = self.get_tool(tool_id)
        self.repo.delete(tool)

        if self.sync:
            self.sync.remove(tool)