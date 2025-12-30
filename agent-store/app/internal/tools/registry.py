from app.contracts.contract_tools import ToolContract, ToolResponseSpec

from typing import Any, Awaitable, Callable, Dict

InternalToolFn = Callable[[dict[str, Any]], Awaitable[Any]]

class InternalToolDef:
    key: str
    contract: ToolContract
    response: ToolResponseSpec
    fn: InternalToolFn

    def __init__(self, key: str, contract: ToolContract, response: ToolResponseSpec, fn: InternalToolFn) -> None:
        self.key = key
        self.contract = contract
        self.response = response
        self.fn = fn

_INTERNAL_TOOLS: Dict[str, InternalToolDef] = {}

def register_internal_tool(tool: InternalToolDef) -> None:
    if tool.key in _INTERNAL_TOOLS:
        raise ValueError(f"Internal tool already registered: {tool.key}")
    _INTERNAL_TOOLS[tool.key] = tool

def get_internal_tool(key: str) -> InternalToolDef:
    try:
        return _INTERNAL_TOOLS[key]
    except KeyError:
        raise KeyError(f"Unknown internal tool: {key}") from None
    
def get_all_internal_tools() -> list[InternalToolDef]:
    return list(_INTERNAL_TOOLS.values())