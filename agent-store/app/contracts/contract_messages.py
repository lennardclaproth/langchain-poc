from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.internal.store.schema import (
    MessageRole,
    ToolCallPayload,
    ToolResultPayload,
)


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chat_id: UUID
    role: MessageRole
    content: str = ""

    tool_call: Optional[ToolCallPayload] = None
    tool_result: Optional[ToolResultPayload] = None
