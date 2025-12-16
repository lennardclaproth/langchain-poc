from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlmodel import Session, select

from app.internal.store.schema import Message


class MessageRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_by_chat(self, chat_id: UUID) -> Sequence[Message]:
        stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc())
        return self.session.exec(stmt).all()

    def create(self, message: Message) -> Message:
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message
