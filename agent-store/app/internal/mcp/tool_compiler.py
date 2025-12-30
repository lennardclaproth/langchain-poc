# app/internal/mcp/tool_compiler.py
from __future__ import annotations
import inspect
import keyword
import re
from typing import Annotated, Any, Awaitable, Callable

from app.internal.store.schema import Tool as DbTool, ToolTransport

DispatchFn = Callable[[DbTool, dict[str, Any]], Awaitable[Any]]

class ToolCompiler:
    """
    
    """
    def __init__(self):
        pass

    _JSON_TO_PY_T = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "object": dict,
        "array": list,
    }

    def _safe_ident(self, name: str) -> str:
        """safe identifier cleans up the identifiers.
        
        It replaces invalid characters that cannot be used by
        python.

        Examples:
            "user-id" -> "user_id"
            "foo bar" -> "foo_bar"
            "λvalue" -> "_value"

        Args:
            name: The name of the identifier.

        Returns:
            A cleaned up identifier to be used in tool compilation.
        """
        name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        if not name or name[0].isdigit() or keyword.iskeyword(name):
            name = f"p_{name}"
        return name

    def compile_tool_fn(self, tool: DbTool, dispatch: DispatchFn) -> Callable[..., Awaitable[Any]]:
        """Compile a tool function based of off the tool
        
        It will compile a new function based off of the tool
        passed in as a param.

        Args:
            tool: The tool from the database that should be compiled.

        Returns:
            An awaitable callable function so that FastMCP can interpret 
            the function.
        """
        # Gets the contract from the tool
        contract = tool.contract or {}
        # Loads the input schema, the input schema is the contract
        # which the user specifies. It follows the MCP JsonRPC schema
        # see: https://modelcontextprotocol.io/specification/2025-11-25/basic
        input_schema = contract.get("input_schema") or {}
        # Get the properties from the input schema
        props: dict[str, dict[str, Any]] = input_schema.get("properties", {}) or {}
        # Decide propertie are static or dynamic. If it has static
        # data it either uses "const" or "x_static" to indicate
        # that the property is static.
        static_props: dict[str, dict[str, Any]] = {}
        dynamic_props: dict[str, dict[str, Any]] = {}
        for raw, spec in props.items():
            is_static = ("const" in spec and spec["const"] is not None) or bool(spec.get("x_static"))
            if is_static:
                static_props[raw] = spec
            else:
                dynamic_props[raw] = spec
        # Get the required properties from the input schema. These are
        # mandatory fields described by the user.
        required = set(input_schema.get("required", []) or [])
        # Creates a name map and sanitizes the variable names for use
        # in the compile function. This map will only contain dynamic
        # properties as static properties are not passed into the compiled 
        # tool function.
        name_map: dict[str, str] = {raw: self._safe_ident(raw) for raw in props.keys()}

        annotations_map: dict[str, Any] = {}
        parameters: list[inspect.Parameter] = []

        # Loop over all dynamic properties and construct the parameters for the
        # function.
        for raw, spec in dynamic_props.items():
            # Get the raw variable name, this is the variable name
            # python is able to understand
            py_name = name_map[raw]
            # Map it to a python type
            base_t = self._JSON_TO_PY_T.get(spec.get("type"), Any)
            # Get the description. This description helps the llm
            # know how to map variables.
            desc = spec.get("description")
            # Create an annotation and add it to the annotations map
            # for efficient O(1) lookup
            ann = Annotated[base_t, desc] if desc else base_t
            annotations_map[py_name] = ann
            # Make sure that required properties are correctly handled
            if raw in required:
                default = inspect._empty
            else:
                default = spec.get("default", None)

            # Construct the function parameter and add it
            # to the parameters
            parameters.append(
                inspect.Parameter(
                    name=py_name,
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default=default,
                    annotation=ann,
                )
            )

        # Create the function signature
        sig = inspect.Signature(parameters)

        # Define the implementation
        async def _impl(*args, **kwargs):
            # Bind the signature to the function
            bound = sig.bind(*args, **kwargs)
            # Set the default values of the bound signature
            bound.apply_defaults()
            # Populate function parameters with the values
            # passed into the function
            packed: dict[str, Any] = {}
            # Inject static properties first into the function
            for raw, spec in static_props.items():
                if "const" in spec:
                    packed[raw] = spec["const"]
                elif "x_static" in spec:
                    packed[raw] = spec["x_static"]
            # Inject dynamic properties into the function
            for raw, py_name in name_map.items():
                val = bound.arguments.get(py_name)
                if val is not None:
                    packed[raw] = val
            # call the injected function and return the result
            return await dispatch(tool, packed)

        # Set the signature and annotation of the implementation
        # function
        _impl.__signature__ = sig  # type: ignore[attr-defined]
        _impl.__annotations__ = annotations_map

        return _impl

