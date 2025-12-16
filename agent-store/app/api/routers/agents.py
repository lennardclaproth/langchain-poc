from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.internal.store.db import get_session
from app.contracts.contracts_agents import AgentCreate, AgentUpdate
from app.internal.store.schema import Agent, Tool
from app.internal.services.service_agents import AgentService
from app.internal.services.errors import NotFoundError, ConflictError, ValidationError

router = APIRouter(prefix="/agents", tags=["agents"])


def _raise_http(err: Exception) -> None:
    if isinstance(err, NotFoundError):
        raise HTTPException(status_code=404, detail=str(err))
    if isinstance(err, ConflictError):
        raise HTTPException(status_code=409, detail=str(err))
    if isinstance(err, ValidationError):
        raise HTTPException(status_code=422, detail=str(err))
    raise err


@router.get("", response_model=List[Agent])
def list_agents(
    enabled: Optional[bool] = None,
    session: Session = Depends(get_session),
):
    svc = AgentService(session)
    return svc.list_agents(enabled=enabled)


@router.get("/{agent_id}", response_model=Agent)
def get_agent(agent_id: UUID, session: Session = Depends(get_session)):
    svc = AgentService(session)
    try:
        return svc.get_agent(agent_id)
    except Exception as e:
        _raise_http(e)


@router.post("", response_model=Agent)
def create_agent(payload: AgentCreate, session: Session = Depends(get_session)):
    svc = AgentService(session)
    try:
        return svc.create_agent(payload)
    except Exception as e:
        _raise_http(e)


@router.patch("/{agent_id}", response_model=Agent)
def update_agent(agent_id: UUID, payload: AgentUpdate, session: Session = Depends(get_session)):
    svc = AgentService(session)
    try:
        return svc.update_agent(agent_id, payload)
    except Exception as e:
        _raise_http(e)


@router.delete("/{agent_id}")
def delete_agent(agent_id: UUID, session: Session = Depends(get_session)):
    svc = AgentService(session)
    try:
        svc.delete_agent(agent_id)
        return {"ok": True}
    except Exception as e:
        _raise_http(e)


@router.get("/{agent_id}/tools", response_model=List[Tool])
def list_agent_tools(agent_id: UUID, session: Session = Depends(get_session)):
    svc = AgentService(session)
    try:
        return svc.list_tools(agent_id)
    except Exception as e:
        _raise_http(e)


@router.post("/{agent_id}/tools/{tool_id}")
def attach_tool(agent_id: UUID, tool_id: UUID, session: Session = Depends(get_session)):
    svc = AgentService(session)
    try:
        svc.attach_tool(agent_id, tool_id)
        return {"ok": True}
    except Exception as e:
        _raise_http(e)


@router.delete("/{agent_id}/tools/{tool_id}")
def detach_tool(agent_id: UUID, tool_id: UUID, session: Session = Depends(get_session)):
    svc = AgentService(session)
    try:
        svc.detach_tool(agent_id, tool_id)
        return {"ok": True}
    except Exception as e:
        _raise_http(e)
