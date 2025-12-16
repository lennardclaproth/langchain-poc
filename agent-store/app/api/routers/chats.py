from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.contracts.contracts_chats import ChatCreate
from app.internal.store.schema import Chat
from app.services.chats import ChatService
from app.services.errors import NotFoundError

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=List[Chat])
def list_chats(agent_id: Optional[UUID] = None, session: Session = Depends(get_session)):
    return ChatService(session).list_chats(agent_id=agent_id)


@router.get("/{chat_id}", response_model=Chat)
def get_chat(chat_id: UUID, session: Session = Depends(get_session)):
    svc = ChatService(session)
    try:
        return svc.get_chat(chat_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=Chat)
def create_chat(payload: ChatCreate, session: Session = Depends(get_session)):
    svc = ChatService(session)
    try:
        return svc.create_chat(payload)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
