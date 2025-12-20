// src/domain/mappers.ts
import type {
    Agent as AgentDto,
    AgentCreate as AgentCreateDto,
    AgentUpdate as AgentUpdateDto,
    AgentModelConfig as AgentModelConfigDto,
    AgentContextTool as AgentContextToolDto,
    Chat as ChatDto,
    Message as MessageDto,
    MessageCreate as MessageCreateDto,
    Tool as ToolDto,
    ToolCreate as ToolCreateDto,
    ToolUpdate as ToolUpdateDto,
    ToolEndpoint as ToolEndpointDto,
    ToolContract as ToolContractDto,
    ToolResponseSpec as ToolResponseSpecDto,
    ToolTransport,
    ToolCallPayload,
    ToolResultPayload,
} from "@/api/store-client/types.gen";

import type {
    Agent,
    AgentCreate,
    AgentUpdate,
    AgentModelConfig,
    AgentContextTool,
    Chat,
    Message,
    MessageCreate,
    Tool,
    ToolCreate,
    ToolUpdate,
    ToolEndpoint,
} from "./api-models";

import { parseDate } from "./api-models";

// ---------------- Agent ----------------
export function toAgent(dto: AgentDto): Agent {
    return {
        id: dto.id ?? "",
        name: dto.name,
        role: dto.role,
        instructions: dto.instructions ?? null,
        enabled: dto.enabled ?? true,
        model: dto.model ? toAgentModelConfig(dto.model as AgentModelConfigDto) : null,
        contextTool: dto.context_tool ? toAgentContextTool(dto.context_tool as AgentContextToolDto) : null,
        createdAt: parseDate(dto.created_at),
        updatedAt: parseDate(dto.updated_at),
    };
}

function toAgentModelConfig(dto: AgentModelConfigDto): AgentModelConfig {
    return {
        provider: dto.provider,
        model: dto.model,
        temperature: dto.temperature,
        maxOutputTokens: dto.max_output_tokens ?? null,
        params: dto.params ?? {},
    };
}

function toAgentContextTool(dto: AgentContextToolDto): AgentContextTool {
    return {
        toolId: dto.tool_id,
        mode: dto.mode,
        config: dto.config ?? {},
    };
}

export function toAgentCreateDto(model: AgentCreate): AgentCreateDto {
    return {
        name: model.name,
        role: model.role,
        instructions: model.instructions ?? null,
        enabled: model.enabled,
        model: model.model ? toAgentModelConfigDto(model.model) : null,
        context_tool: model.contextTool ? toAgentContextToolDto(model.contextTool) : null,
    };
}

export function toAgentUpdateDto(model: AgentUpdate): AgentUpdateDto {
    return {
        name: model.name ?? null,
        role: model.role ?? null,
        instructions: model.instructions ?? null,
        enabled: model.enabled ?? null,
        model: model.model ? toAgentModelConfigDto(model.model) : null,
        context_tool: model.contextTool ? toAgentContextToolDto(model.contextTool) : null,
    };
}

function toAgentModelConfigDto(model: AgentModelConfig): AgentModelConfigDto {
    return {
        provider: model.provider,
        model: model.model,
        temperature: model.temperature,
        max_output_tokens: model.maxOutputTokens ?? null,
        params: model.params ?? {},
    };
}

function toAgentContextToolDto(model: AgentContextTool): AgentContextToolDto {
    return {
        tool_id: model.toolId,
        mode: model.mode,
        config: model.config ?? {},
    };
}

// ---------------- Chat ----------------
export function toChat(dto: ChatDto): Chat {
    return {
        id: dto.id ?? "",
        agentId: dto.agent_id,
        createdAt: parseDate(dto.created_at),
        updatedAt: parseDate(dto.updated_at),
    };
}

// ---------------- Message ----------------
export function toMessage(dto: MessageDto): Message {
    return {
        id: dto.id ?? "",
        chatId: dto.chat_id,
        role: dto.role,
        content: dto.content ?? "",
        toolCall: (dto.tool_call as ToolCallPayload | null) ?? null,
        toolResult: (dto.tool_result as ToolResultPayload | null) ?? null,
        createdAt: parseDate(dto.created_at),
    };
}

export function toMessageCreateDto(model: MessageCreate): MessageCreateDto {
    return {
        chat_id: model.chatId,
        role: model.role,
        content: model.content,
        tool_call: model.toolCall ?? null,
        tool_result: model.toolResult ?? null,
    };
}

export function toToolEndpoint(dto: ToolEndpointDto): ToolEndpoint {
    // transport is required in dto
    if (dto.transport === "http") {
        // server validator requires url+method for http, but TS says optional, so we normalize
        return {
            transport: "http",
            url: dto.url ?? "",
            method: (dto.method ?? "GET") as NonNullable<ToolEndpointDto["method"]>,
            headers: dto.headers ?? {},
            target: dto.target ?? null,
        };
    }

    if (dto.transport === "mcp") {
        return {
            transport: "mcp",
            mcpServer: dto.mcp_server ?? "",
            mcpTool: dto.mcp_tool ?? "",
        };
    }

    return {
        transport: "internal",
        target: dto.target ?? null,
    };
}

export function toToolEndpointDto(model: ToolEndpoint): ToolEndpointDto {
    if (model.transport === "http") {
        return {
            transport: "http",
            url: model.url,
            method: model.method,
            headers: model.headers ?? {},
            target: model.target ?? null,
        };
    }
    if (model.transport === "mcp") {
        return {
            transport: "mcp",
            mcp_server: model.mcpServer,
            mcp_tool: model.mcpTool,
        };
    }
    return {
        transport: "internal",
        target: model.target ?? null,
    };
}

// ---------------- Tool ----------------
// Important: your Tool DTO currently has endpoint/contract/response as `{[k:string]:unknown}`.
// We map endpoint if present by *attempting* ToolEndpoint shape.
// For contract/response we just pass through (typed as structured OR record).
export function toTool(dto: ToolDto): Tool {
    const endpointRaw = dto.endpoint as unknown;

    // If backend actually returns ToolEndpoint-compatible JSON, map it.
    // Otherwise keep null.
    const endpoint =
        endpointRaw && typeof endpointRaw === "object" && "transport" in (endpointRaw as any)
            ? toToolEndpoint(endpointRaw as ToolEndpointDto)
            : null;

    return {
        id: dto.id ?? "",
        name: dto.name,
        description: dto.description,
        enabled: dto.enabled ?? true,
        endpoint,
        contract: (dto.contract as ToolContractDto | Record<string, unknown> | undefined) ?? null,
        response: (dto.response as ToolResponseSpecDto | Record<string, unknown> | undefined) ?? null,
        createdAt: parseDate(dto.created_at),
        updatedAt: parseDate(dto.updated_at),
    };
}

export function toToolCreateDto(model: ToolCreate): ToolCreateDto {
    return {
        name: model.name,
        description: model.description,
        enabled: model.enabled,
        endpoint: model.endpoint ? toToolEndpointDto(model.endpoint) : null,
        contract: (model.contract as any) ?? null,
        response: (model.response as any) ?? null,
    };
}

export function toToolUpdateDto(model: ToolUpdate): ToolUpdateDto {
    return {
        name: model.name ?? null,
        description: model.description ?? null,
        enabled: model.enabled ?? null,
        endpoint: model.endpoint ? toToolEndpointDto(model.endpoint) : null,
        contract: (model.contract as any) ?? null,
        response: (model.response as any) ?? null,
    };
}
