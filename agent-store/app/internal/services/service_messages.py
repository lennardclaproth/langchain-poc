from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session

from app.contracts.contract_messages import MessageCreate
from app.internal.store.schema import Message
from app.internal.store.repository_chats import ChatRepository
from app.internal.store.repository_messages import MessageRepository

from .errors import NotFoundError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MessageService:
    def __init__(self, session: Session):
        self.repo = MessageRepository(session)
        self.chats = ChatRepository(session)

    def list_messages(self, chat_id: UUID):
        chat = self.chats.get_by_id(chat_id)
        if not chat:
            raise NotFoundError(resource="Chat", identifier=str(chat_id))
        return self.repo.list_by_chat(chat_id)

    def add_message(self, payload: MessageCreate) -> Message:
        chat = self.chats.get_by_id(payload.chat_id)
        if not chat:
            raise NotFoundError(resource="Chat", identifier=str(payload.chat_id))

        msg = Message(
            chat_id=payload.chat_id,
            role=payload.role,
            content=payload.content or "",
            created_at=utcnow(),
        )

        if payload.tool_call is not None:
            msg.set_tool_call(payload.tool_call)

        if payload.tool_result is not None:
            msg.set_tool_result(payload.tool_result)

        # touch chat updated_at
        chat.updated_at = utcnow()
        self.chats.touch(chat)

        return self.repo.create(msg)
