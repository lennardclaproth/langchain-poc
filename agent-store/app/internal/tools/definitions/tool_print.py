from __future__ import annotations

from typing import Any, Dict

from app.contracts.spec_tools import ToolContract, ToolInputSchema, ToolResponseSpec, JsonSchemaProperty, JsonType
from app.internal.tools.registry import InternalToolDef, register_internal_tool

# Define the tool contract
PRINT_CONTRACT = ToolContract(
    input_schema=ToolInputSchema(
        properties={
            "text": JsonSchemaProperty(
                type="string",  # type: JsonType
                description="Text to print",
            ),
            "prefix": JsonSchemaProperty(
                type="string",  # type: JsonType
                description="Prefix configured when saving the tool template",
                default="[SYSTEM] ",
                x_static=True,
            ),
        },
        required=["text"],
        additionalProperties=False,
    ),
    tags=["internal", "debug"],
    read_only=True,
    idempotent=True,
)

# Define the response schema
PRINT_RESPONSE_SPEC = ToolResponseSpec(
    schema={
        "type": "object",
        "properties": {
            "printed": {
                "type": "boolean",
                "description": "Whether the text was printed",
            },
            "text": {
                "type": "string",
                "description": "The text that was printed",
            },
        },
    },
    format="json",
)


async def internal_print(text: str, prefix: str = "[SYSTEM] ", **kwargs) -> Dict[str, Any]:
    """
    Print text to stdout (for debugging/logging purposes).
    
    :param text: The text to print
    :param prefix: Optional prefix to prepend to the text
    :return: Confirmation dictionary
    """
    output = f"{prefix}{text}"
    print(output)
    return {
        "printed": True,
        "text": output,
    }


# Create and register the tool definition
PRINT_TOOL = InternalToolDef(
    key="internal.print",
    contract=PRINT_CONTRACT,
    response=PRINT_RESPONSE_SPEC,
    fn=internal_print,
)

register_internal_tool(PRINT_TOOL)
