# app/api/routes/tools.py
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.internal.store.db import get_session
from app.contracts.contract_tools import ToolCreate, ToolUpdate
from app.internal.services.service_tools import ToolService

router = APIRouter(prefix="/tools", tags=["tools"])

@router.post("", status_code=201)
def create_tool(payload: ToolCreate, session: Session = Depends(get_session)):
    return ToolService(session).create_tool(payload)

@router.get("/{tool_id}")
def get_tool(tool_id: UUID, session: Session = Depends(get_session)):
    return ToolService(session).get_tool(tool_id)

@router.patch("/{tool_id}")
def update_tool(tool_id: UUID, payload: ToolUpdate, session: Session = Depends(get_session)):
    return ToolService(session).update_tool(tool_id, payload)

@router.delete("/{tool_id}", status_code=204)
def delete_tool(tool_id: UUID, session: Session = Depends(get_session)):
    ToolService(session).delete_tool(tool_id)
    return None
