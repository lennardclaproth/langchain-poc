from app.contracts.spec_tools import ToolContract, ToolInputSchema, JsonSchemaProperty, ToolResponseSpec

PRINT_CONTRACT = ToolContract(
    input_schema=ToolInputSchema(
        properties={
            "text": JsonSchemaProperty(type="string", description="Text to print"),
            "prefix": JsonSchemaProperty(
                type="string",
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

PRINT_RESPONSE_SPEC = ToolResponseSpec(
    format="json",
    schema={
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
        },
        "required": ["ok"],
        "additionalProperties": True
    }
)