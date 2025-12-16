from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: UUID
