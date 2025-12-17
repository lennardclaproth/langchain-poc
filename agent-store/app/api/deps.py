# app/api/deps.py
from fastapi import Depends, Request
from sqlmodel import Session

from app.internal.store import db
from app.internal.services.service_tools import ToolService
from app.internal.services.service_agents import AgentService
from app.internal.services.service_chats import ChatService
from app.internal.services.service_messages import MessageService

def get_session():
    with Session(db.engine) as s:
        yield s

def get_tool_service(
    request: Request,
    session: Session = Depends(get_session),
) -> ToolService:
    sync = getattr(request.app.state, "tool_sync", None)
    return ToolService(session, sync=sync)

def get_agent_service(
        session: Session = Depends(get_session)
) -> AgentService:
    return AgentService(session)

def get_message_service(
        session: Session = Depends(get_session)
) -> MessageService:
    return MessageService(session)

def get_chat_service(
        session: Session = Depends(get_session)
) -> ChatService:
    return ChatService(session)