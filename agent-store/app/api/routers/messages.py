from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.contracts.contracts_messages import MessageCreate
from app.internal.store.schema import Message
from app.services.messages import MessageService
from app.services.errors import NotFoundError

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/by-chat/{chat_id}", response_model=List[Message])
def list_messages(chat_id: UUID, session: Session = Depends(get_session)):
    svc = MessageService(session)
    try:
        return svc.list_messages(chat_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=Message)
def add_message(payload: MessageCreate, session: Session = Depends(get_session)):
    svc = MessageService(session)
    try:
        return svc.add_message(payload)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
