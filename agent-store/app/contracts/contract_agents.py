from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.internal.store.schema import AgentModelConfig, AgentContextTool


class AgentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    role: str
    instructions: Optional[str] = None
    enabled: bool = True

    model: Optional[AgentModelConfig] = None
    context_tool: Optional[AgentContextTool] = None


class AgentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    role: Optional[str] = None
    instructions: Optional[str]
    enabled: Optional[bool] = None

    model: Optional[AgentModelConfig] = None
    context_tool: Optional[AgentContextTool] = None
