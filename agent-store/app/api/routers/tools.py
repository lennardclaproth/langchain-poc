from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.internal.store.db import get_session
from app.contracts.contract_tools import CreateToolRequest, ToolResponse, UpdateToolRequest
from app.internal.services.service_tools import ToolService
from app.api.deps import get_tool_service

router = APIRouter(prefix="/tools", tags=["tools"])

@router.post("", status_code=201, response_model=ToolResponse, response_model_exclude_none=True)
async def create_tool(payload: CreateToolRequest, svc: ToolService = Depends(get_tool_service)):
    return await svc.create_tool(payload)

@router.get("", status_code=200, response_model=List[ToolResponse], response_model_exclude_none=True)
def list_tools(service: ToolService = Depends(get_tool_service)):
    return service.get_all_tools()

@router.get("/internal-available", status_code=200, response_model=List[ToolResponse], response_model_exclude_none=True)
async def get_internal_available_tools(svc: ToolService = Depends(get_tool_service)):
    return await svc.get_available_internal_tools()

@router.get("/{tool_id}", status_code=200, response_model=ToolResponse, response_model_exclude_none=True)
def get_tool(tool_id: UUID, svc: ToolService = Depends(get_tool_service)):
    return svc.get_tool(tool_id)

@router.patch("/{tool_id}")
async def update_tool(tool_id: UUID, payload: UpdateToolRequest, svc: ToolService = Depends(get_tool_service)):
    return await svc.update_tool(tool_id, payload)

@router.delete("/{tool_id}", status_code=204)
async def delete_tool(tool_id: UUID, svc: ToolService = Depends(get_tool_service)):
    await svc.delete_tool(tool_id)
    return None
