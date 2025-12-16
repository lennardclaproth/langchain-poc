from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlmodel import Session, select

from app.internal.store.schema import Chat


class ChatRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, chat_id: UUID) -> Optional[Chat]:
        return self.session.get(Chat, chat_id)

    def list(self, *, agent_id: Optional[UUID] = None) -> Sequence[Chat]:
        stmt = select(Chat)
        if agent_id is not None:
            stmt = stmt.where(Chat.agent_id == agent_id)
        return self.session.exec(stmt).all()

    def create(self, chat: Chat) -> Chat:
        self.session.add(chat)
        self.session.commit()
        self.session.refresh(chat)
        return chat

    def touch(self, chat: Chat) -> Chat:
        self.session.add(chat)
        self.session.commit()
        self.session.refresh(chat)
        return chat
