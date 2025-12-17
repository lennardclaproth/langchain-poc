# app/api/routes/tools.py
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.internal.store.db import get_session
from app.contracts.contract_tools import ToolCreate, ToolUpdate
from app.internal.services.service_tools import ToolService
from app.api.deps import get_tool_service

router = APIRouter(prefix="/tools", tags=["tools"])

@router.post("", status_code=201)
def create_tool(payload: ToolCreate, svc: ToolService = Depends(get_tool_service)):
    return svc.create_tool(payload)

@router.get("")
def list_tools(service: ToolService = Depends(get_tool_service)):
    return service.get_all_tools()

@router.get("/{tool_id}")
def get_tool(tool_id: UUID, svc: ToolService = Depends(get_tool_service)):
    return svc.get_tool(tool_id)

@router.patch("/{tool_id}")
def update_tool(tool_id: UUID, payload: ToolUpdate, svc: ToolService = Depends(get_tool_service)):
    return svc.update_tool(tool_id, payload)

@router.delete("/{tool_id}", status_code=204)
def delete_tool(tool_id: UUID, svc: ToolService = Depends(get_tool_service)):
    svc.delete_tool(tool_id)
    return None
