# app/api/v1/chat.py
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.internal.services.service_agents import (
    AgentRuntimeService,
    AgentRuntimeServiceConfig,
    AgentDisabled,
)

router = APIRouter(tags=["chat"])

# Ideally you create this once at app startup (dependency injection),
# but this is the simplest working version.
svc = AgentRuntimeService(
    AgentRuntimeServiceConfig(
        agent_store_base_url="http://localhost:8000",
        mcp_url="http://localhost:8000/mcp",
    )
)


@router.get("/{agent_id}/run")
async def run_agent(
    agent_id: UUID,
    message: str = Query(..., description="User message"),
):
    try:
        return await svc.run(agent_id=agent_id, message=message)

    except AgentDisabled as e:
        raise HTTPException(status_code=403, detail=str(e))

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    except ValueError as e:
        # used for "not found" in the service example
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        # fallback
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
