from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlmodel import Session

from app.contracts.contract_chats import ChatCreate
from app.internal.store.schema import Chat
from app.internal.store.repository_agents import AgentRepository
from app.internal.store.repository_chats import ChatRepository

from .errors import NotFoundError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChatService:
    def __init__(self, session: Session):
        self.repo = ChatRepository(session)
        self.agents = AgentRepository(session)

    def list_chats(self, *, agent_id: Optional[UUID] = None) -> Sequence[Chat]:
        return self.repo.list(agent_id=agent_id)

    def get_chat(self, chat_id: UUID) -> Chat:
        chat = self.repo.get_by_id(chat_id)
        if not chat:
            raise NotFoundError(resource="Chat", identifier=str(chat_id))
        return chat

    def create_chat(self, payload: ChatCreate) -> Chat:
        agent = self.agents.get_by_id(payload.agent_id)
        if not agent:
            raise NotFoundError(resource="Agent", identifier=str(payload.agent_id))

        chat = Chat(
            agent_id=payload.agent_id,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        return self.repo.create(chat)
