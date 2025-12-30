# app/services/service_tools.py
from __future__ import annotations

from typing import Any, Dict, Set
from uuid import UUID

from sqlmodel import Session

from app.contracts.contract_tools import CreateToolRequest, ToolResponse, UpdateToolRequest
from app.contracts.spec_tools import ToolEndpoint, ToolContract, _validate_value_against_property
from app.internal.store.schema import Tool, ToolTransport
from app.internal.store.repository_tools import ToolRepository
from app.internal.tools import registry
from .errors import ConflictError, NotFoundError, ValidationError
from .ports import ToolSyncPort
from .mappers import map_tool_to_response

class ToolService:
    def __init__(self, session: Session, sync: ToolSyncPort | None = None):
        self.repo = ToolRepository(session)
        self.sync = sync


    def _validate_endpoint(self, endpoint : ToolEndpoint) -> None:
        """
        Validates the tool endpoint based on its transport type and checks
        the required fields per transport.
        
        :param self: The current instance of the class.
        :param endpoint: The endpoint to validate.
        """
        if endpoint.transport == ToolTransport.http:
            if endpoint.url is None or not endpoint.method:
                raise ValidationError("HTTP transport requires endpoint.url and endpoint.method")

        elif endpoint.transport == ToolTransport.mcp:
            if not endpoint.mcp_server or not endpoint.mcp_tool:
                raise ValidationError("MCP transport requires endpoint.mcp_server and endpoint.mcp_tool")

        # Make sure that internal transport has the target field
        elif endpoint.transport == ToolTransport.internal:
            if not endpoint.target:
                raise ValidationError("Internal transport requires endpoint.target")

        else:
            raise ValidationError(f"Unknown transport '{endpoint.transport}'")

    async def get_available_internal_tools(self) -> list[ToolResponse]:
        """
        Returns a list of all available internal tools from the registry.
        
        :return: List of available internal tools
        :rtype: list[ToolResponse]
        """
        
        internal_tools = registry.get_all_internal_tools()
        
        return [
            ToolResponse(
                name=tool.key,
                transport="internal",
                contract=tool.contract,
                response=tool.response
            )
            for tool in internal_tools
        ]

    async def create_tool(self, payload: CreateToolRequest) -> ToolResponse:
        transport = payload.endpoint.transport

        if transport == ToolTransport.http:
            return await self._create_http_tool(payload)
        elif transport == ToolTransport.mcp:
            raise NotImplementedError("MCP tool creation not yet implemented")
        elif transport == ToolTransport.internal:
            return await self._create_internal_tool(payload)
        else:
            raise ValidationError(f"Unknown transport '{transport}'")

    async def _create_internal_tool(self, payload: CreateToolRequest) -> ToolResponse:
        """
        Creates an internal tool. An internal tool is a tool that maps
        to a predefined function within the application.
        
        :param self: The current instance of the class.
        :param payload: The payload containing the data needed to create an internal tool
        :type payload: ToolCreate
        :return: The tool that was created.
        :rtype: Tool
        """
        # Check if a tool with the same name already exists.
        existing = self.repo.get_by_name(payload.name)
        if existing:
            raise ConflictError(resource="Tool", field="name", value=payload.name)
        # If the payload endpoint is missing, we raise a validation error
        if payload.endpoint is None:
            raise ValidationError(message="Internal tools require 'endpoint'.")
        endpoint: ToolEndpoint = payload.endpoint
        # Make sure the transport is internal
        if endpoint.transport != ToolTransport.internal:
            raise ValidationError(message="Endpoint transport must be 'internal'.")
        # validates internal endpoint fields too (internal_tool required, etc.)
        self._validate_endpoint(endpoint)
        # validate_endpoint mkaes sure that target is present
        internal_key = endpoint.target
        
        # Gets the internal tool definition from the registry.
        try:
            internal_def = registry.get_internal_tool(internal_key)
        except KeyError:
            raise ValidationError(message=f"Unknown internal tool: {internal_key}")

        registry_contract: ToolContract = internal_def.contract

        # Make sure contract is empty considering we get it from the registry
        if payload.contract is not None:
            raise ValidationError(
                    message="Cannot provide contract for internal tools."
                )
        # Make sure response is empty considering we get it from the registry
        if payload.response is not None:
            raise ValidationError(
                    message="Cannot provide resposne model for internal tools."
                )

        contract_to_store = registry_contract

        # Extract which properties have the attribute x_static=True in the contract schema
        schema = contract_to_store.input_schema
        static_keys: Set[str] = {
            k for k, prop in schema.properties.items() if getattr(prop, "x_static", False)
        }
        # Get static inputs from the endpoint configuration, these contain the values 
        # to which it should be mapped.
        provided_static: Dict[str, Any] = getattr(endpoint, "static_inputs", None) or {}
        # Throw validation error if provided static inputs contain keys that are not part
        # of the properties that are marked as static.
        unknown_static = [k for k in provided_static.keys() if k not in static_keys]
        if unknown_static:
            raise ValidationError(message=f"static_inputs contains non-static keys: {unknown_static}")

        # Initiate a dict to populate the contract properties with the values of the endpoint.
        final_static: Dict[str, Any] = {}
        # For each static property of the contracts
        for k in static_keys:
            # Get the property definition from the contract schema
            prop = schema.properties[k]
            # Check if a static value was provided in the endpoint
            if k in provided_static:
                val = provided_static[k]
            #If there was no value provided, check the default value of the property
            elif prop.default is not None:
                val = prop.default
            else:
                # Throw validation error if no value or default value is found
                raise ValidationError(message=f"Missing static input '{k}' and no default is configured.")
            # Validate the value against the property definition
            errs = _validate_value_against_property(val, prop, path=f"static_inputs.{k}")
            if errs:
                raise ValidationError(message="; ".join(errs[:5]))
            # Set the value
            final_static[k] = val

        # Persist the computed static values into endpoint
        endpoint.static_inputs = final_static
        # Store the tool
        tool = self.repo.create(
            name=payload.name,
            description=payload.description,
            enabled=payload.enabled,
            endpoint=endpoint,
            contract=contract_to_store,
            response=internal_def.response,
        )
        # Make sure the MCP server is in sync
        if self.sync:
            await self.sync.upsert(tool)

        return map_tool_to_response(tool)

    async def _create_http_tool(self, payload: CreateToolRequest) -> ToolResponse:
        """
        Docstring for _create_http_tool
        
        :param self: The current instance of the class.
        :param payload: The payload containing the data needed to create an HTTP tool
        :type payload: ToolCreate
        :return: The http tool that was created.
        :rtype: Tool
        """
        # Check if a tool with the same name already exists.
        existing = self.repo.get_by_name(payload.name)
        if existing:
            raise ConflictError(resource="Tool", field="name", value=payload.name)
        # Make sure the endpoint is correctly configured
        self._validate_endpoint(payload.endpoint)
        # Store the tool
        tool = self.repo.create(
            name=payload.name,
            description=payload.description,
            enabled=payload.enabled,
            endpoint=payload.endpoint,
            contract=payload.contract,
            response=payload.response,
        )
        # Make sure the MCP server is in sync
        if self.sync:
            await self.sync.upsert(tool)

        return map_tool_to_response(tool)

    def get_tool(self, tool_id: UUID) -> ToolResponse:
        tool = self.repo.get_by_id(tool_id)
        if not tool:
            raise NotFoundError(resource="Tool", identifier=str(tool_id))
        return map_tool_to_response(tool)

    async def update_tool(self, tool_id: UUID, payload: UpdateToolRequest) -> ToolResponse:
        tool = self.repo.get_by_id(tool_id)
        if not tool:
            raise NotFoundError(resource="Tool", identifier=str(tool_id))

        if payload.name and payload.name != tool.name:
            if self.repo.get_by_name(payload.name):
                raise ConflictError(resource="Tool", field="name", value=payload.name)

        if payload.endpoint is not None:
            self._validate_endpoint(payload.endpoint)

        tool = self.repo.update(
            tool,
            name=payload.name,
            description=payload.description,
            enabled=payload.enabled,
            endpoint=payload.endpoint,
            contract=payload.contract,
            response=payload.response,
        )

        if self.sync:
            await self.sync.upsert(tool)

        return map_tool_to_response(tool)

    def get_all_tools(self) -> list[ToolResponse]:
        tools = self.repo.get_all()
        return [map_tool_to_response(tool) for tool in tools]

    async def delete_tool(self, tool_id: UUID) -> None:
        tool = self.repo.get_by_id(tool_id)
        if not tool:
            raise NotFoundError(resource="Tool", identifier=str(tool_id))
        self.repo.delete(tool)

        if self.sync:
            await self.sync.remove(tool)