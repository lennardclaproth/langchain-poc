from typing import Any

from langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse
)
from langgraph.runtime import Runtime

class Middleware(AgentMiddleware):
    def __init__(self):
        super().__init__()

    async def abefore_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"About to call model with {len(state['messages'])} messages")
        return None
    
    async def awrap_tool_call(self, request, handler):
        result = await handler(request)
        return result
    
    async def awrap_model_call(self, request, handler):
        result = await handler(request)
        return result

    async def aafter_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"Model returned: {state['messages'][-1].content}")
        return None