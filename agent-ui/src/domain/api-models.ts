// src/domain/api-models.ts
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
} from "@/api/store-client/types.gen.ts";

// ---------- helpers ----------
export type IsoDateString = string;

export const parseDate = (s?: IsoDateString | null): Date | null => {
  if (!s) return null;
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? null : d;
};

export const toIso = (d?: Date | null): string | undefined => {
  if (!d) return undefined;
  const iso = d.toISOString();
  return iso;
};

// ---------- Agent domain ----------
export type Agent = {
  id: string;
  name: string;
  role: string;
  instructions: string | null;
  enabled: boolean;
  model: AgentModelConfig | null;
  contextTool: AgentContextTool | null;
  createdAt: Date | null;
  updatedAt: Date | null;
};

export type AgentModelConfig = {
  provider?: string;
  model: string;
  temperature?: number;
  maxOutputTokens?: number | null;
  params?: Record<string, unknown>;
};

export type AgentContextTool = {
  toolId: string;
  mode?: "system" | "user" | "tool";
  config?: Record<string, unknown>;
};

export type AgentCreate = {
  name: string;
  role: string;
  instructions?: string | null;
  enabled?: boolean;
  model?: AgentModelConfig | null;
  contextTool?: AgentContextTool | null;
};

export type AgentUpdate = {
  name?: string | null;
  role?: string | null;
  instructions?: string | null;
  enabled?: boolean | null;
  model?: AgentModelConfig | null;
  contextTool?: AgentContextTool | null;
};

// ---------- Chat domain ----------
export type Chat = {
  id: string;
  agentId: string;
  createdAt: Date | null;
  updatedAt: Date | null;
};

export type Message = {
  id: string;
  chatId: string;
  role: MessageDto["role"];
  content: string;
  toolCall: ToolCallPayload | null;
  toolResult: ToolResultPayload | null;
  createdAt: Date | null;
};

export type MessageCreate = {
  chatId: string;
  role: MessageDto["role"];
  content?: string;
  toolCall?: ToolCallPayload | null;
  toolResult?: ToolResultPayload | null;
};

// ---------- Tool domain ----------
// Give ToolEndpoint a discriminated union so Vue can render safely
export type ToolEndpoint =
  | {
      transport: "http";
      url: string;
      method: NonNullable<ToolEndpointDto["method"]>;
      headers: Record<string, string>;
      target?: string | null;
    }
  | {
      transport: "mcp";
      mcpServer: string;
      mcpTool: string;
    }
  | {
      transport: "internal";
      target?: string | null;
    };

// Keep contract/response typed if you want; they exist in your generated types.
// BUT your generated ToolDto currently uses `{[k:string]:unknown}` for these,
// so we store them as structured where possible.
export type Tool = {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  endpoint: ToolEndpoint | null;
  contract: ToolContractDto | Record<string, unknown> | null;
  response: ToolResponseSpecDto | Record<string, unknown> | null;
  createdAt: Date | null;
  updatedAt: Date | null;
};

export type ToolCreate = {
  name: string;
  description: string;
  enabled?: boolean;
  endpoint?: ToolEndpoint | null;
  contract?: ToolContractDto | Record<string, unknown> | null;
  response?: ToolResponseSpecDto | Record<string, unknown> | null;
};

export type ToolUpdate = {
  name?: string | null;
  description?: string | null;
  enabled?: boolean | null;
  endpoint?: ToolEndpoint | null;
  contract?: ToolContractDto | Record<string, unknown> | null;
  response?: ToolResponseSpecDto | Record<string, unknown> | null;
};
