from contextlib import suppress
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.contracts.spec_tools import ToolContract, ToolEndpoint, ToolResponseSpec, ToolTransport

from pydantic import BaseModel, Field as PydanticField, HttpUrl, ConfigDict
from sqlalchemy import Column
from sqlalchemy.orm import Mapped
from sqlalchemy.types import JSON
from sqlmodel import Field, Relationship, SQLModel

class AgentModelConfig(BaseModel):
    provider: str = "ollama"
    model: str
    temperature: float = 0.2
    max_output_tokens: Optional[int] = 512
    params: Dict[str, Any] = PydanticField(default_factory=dict)


class ContextInjectionMode(str, Enum):
    system = "system"
    user = "user"
    tool = "tool"


class AgentContextTool(BaseModel):
    tool_id: UUID
    mode: ContextInjectionMode = ContextInjectionMode.system
    config: Dict[str, Any] = PydanticField(default_factory=dict)


class MessageRole(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
    tool_call = "tool_call"
    tool_result = "tool_result"


class ToolCallPayload(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = PydanticField(default_factory=dict)
    call_id: Optional[str] = None


class ToolResultPayload(BaseModel):
    tool_name: str
    result: Any = None
    call_id: Optional[str] = None
    is_error: bool = False
    error_message: Optional[str] = None


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# -------------------------
# SQLModel tables
# -------------------------
# IMPORTANT: define link model before using it in Relationship(link_model=...)
class AgentToolLink(SQLModel, table=True):
    __tablename__ = "agent_tools"

    agent_id: UUID = Field(foreign_key="agents.id", primary_key=True)
    tool_id: UUID = Field(foreign_key="tools.id", primary_key=True)


class Tool(SQLModel, table=True):
    __tablename__ = "tools"
    __allow_unmapped__ = True


    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(index=True, unique=True)
    description: str
    enabled: bool = Field(default=True, index=True)

    endpoint: Dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    contract: Dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    response: Dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    agents: list["Agent"] = Relationship(
        back_populates="tools",
        link_model=AgentToolLink,
    )

    # Convenience helpers
    def set_endpoint(self, endpoint: ToolEndpoint) -> None:
        self.endpoint = endpoint.model_dump(mode="json", by_alias=True)

    def get_endpoint(self) -> ToolEndpoint:
        return ToolEndpoint.model_validate(self.endpoint)

    def set_contract(self, contract: ToolContract) -> None:
        self.contract = contract.model_dump(mode="json", by_alias=True)

    def get_contract(self) -> ToolContract:
        return ToolContract.model_validate(self.contract)

    def set_response(self, response: ToolResponseSpec) -> None:
        self.response = response.model_dump(mode="json", by_alias=True)

    def get_response(self) -> ToolResponseSpec:
        return ToolResponseSpec.model_validate(self.response)


class Agent(SQLModel, table=True):
    __tablename__ = "agents"
    __allow_unmapped__ = True

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(index=True)
    role: str
    enabled: bool = Field(default=True, index=True)

    model: Dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    context_tool: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON), default=None)

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    tools: list["Tool"] = Relationship(
        back_populates="agents",
        link_model=AgentToolLink,
    )
    chats: list["Chat"] = Relationship(back_populates="agent")

    # Convenience
    def set_model(self, cfg: AgentModelConfig) -> None:
        self.model = cfg.model_dump(mode="json", by_alias=True)

    def get_model(self) -> AgentModelConfig:
        return AgentModelConfig.model_validate(self.model)

    def set_context_tool(self, ctx: Optional[AgentContextTool]) -> None:
        self.context_tool = None if ctx is None else ctx.model_dump(mode="json", by_alias=True)

    def get_context_tool(self) -> Optional[AgentContextTool]:
        return None if self.context_tool is None else AgentContextTool.model_validate(self.context_tool)


class Chat(SQLModel, table=True):
    __tablename__ = "chats"
    __allow_unmapped__ = True

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    agent_id: UUID = Field(foreign_key="agents.id", index=True)

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    agent: Optional["Agent"] = Relationship(back_populates="chats")
    messages: list["Message"] = Relationship(back_populates="chat")


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    __allow_unmapped__ = True

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    chat_id: UUID = Field(foreign_key="chats.id", index=True)

    role: MessageRole = Field(index=True)
    content: str = Field(default="")

    tool_call: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON), default=None)
    tool_result: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON), default=None)

    created_at: datetime = Field(default_factory=utcnow)

    chat: Optional["Chat"] = Relationship(back_populates="messages")

    # Convenience
    def set_tool_call(self, payload: Optional[ToolCallPayload]) -> None:
        self.tool_call = None if payload is None else payload.model_dump(mode="json", by_alias=True)

    def get_tool_call(self) -> Optional[ToolCallPayload]:
        return None if self.tool_call is None else ToolCallPayload.model_validate(self.tool_call)

    def set_tool_result(self, payload: Optional[ToolResultPayload]) -> None:
        self.tool_result = None if payload is None else payload.model_dump(mode="json", by_alias=True)

    def get_tool_result(self) -> Optional[ToolResultPayload]:
        return None if self.tool_result is None else ToolResultPayload.model_validate(self.tool_result)
