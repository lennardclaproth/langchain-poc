from typing import Optional

from app.contracts.contract_tools import ToolResponse
from app.internal.store.schema import Tool, ToolTransport


def map_tool_to_response(tool: Tool) -> ToolResponse:
    """
    Maps a Tool database model to a ToolResponse contract model.
    
    Deserializes the JSON fields (endpoint, contract, response) from the
    database into their structured Pydantic models.
    
    :param tool: The Tool database model
    :type tool: Tool
    :return: The mapped ToolResponse model
    :rtype: ToolResponse
    """
    # Extract transport type from endpoint if available
    transport: str = "unknown"
    if tool.endpoint:
        endpoint = tool.get_endpoint()
        transport = endpoint.transport.value if hasattr(endpoint.transport, "value") else str(endpoint.transport)
    
    # Deserialize the structured models from JSON dicts
    endpoint = tool.get_endpoint() if tool.endpoint else None
    contract = tool.get_contract() if tool.contract else None
    response = tool.get_response() if tool.response else None
    
    return ToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        enabled=tool.enabled,
        transport=transport,
        endpoint=endpoint,
        contract=contract,
        response=response,
        created_at=tool.created_at,
        updated_at=tool.updated_at,
    )
