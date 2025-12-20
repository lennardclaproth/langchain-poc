// src/domain/repos.ts
import {
    listAgentsAgentsGet,
    getAgentAgentsAgentIdGet,
    createAgentAgentsPost,
    updateAgentAgentsAgentIdPatch,
    deleteAgentAgentsAgentIdDelete,
    listChatsChatsGet,
    createChatChatsPost,
    getChatChatsChatIdGet,
    listMessagesMessagesByChatChatIdGet,
    addMessageMessagesPost,
    listAgentToolsAgentsAgentIdToolsGet,
    // tools endpoints exist but responses are unknown in your types, see below
    listToolsToolsGet,
    getToolToolsToolIdGet,
    createToolToolsPost,
    updateToolToolsToolIdPatch,
    deleteToolToolsToolIdDelete,
} from "@/api/store-client/sdk.gen";

import type { Agent, AgentCreate, AgentUpdate, Chat, Message, MessageCreate, Tool, ToolCreate, ToolUpdate } from "./api-models";
import { toAgent, toAgentCreateDto, toAgentUpdateDto, toChat, toMessage, toMessageCreateDto, toTool, toToolCreateDto, toToolUpdateDto } from "./mappers";

// ----- Agents -----
export async function listAgents(enabled?: boolean | null): Promise<Agent[]> {
    const res = await listAgentsAgentsGet({ query: enabled == null ? undefined : { enabled } });
    const data = res.data
    if (!Array.isArray(data)) return []
    return data.map(toAgent);
}

export async function getAgent(agentId: string): Promise<Agent> {
    const res = await getAgentAgentsAgentIdGet({ path: { agent_id: agentId } });
    const data = res.data
    if (data == null || data == undefined) throw Error("data in get agent is undefined")
    return toAgent(res.data);
}

export async function createAgent(payload: AgentCreate): Promise<Agent> {
    const res = await createAgentAgentsPost({ body: toAgentCreateDto(payload) });
    const data = res.data
    if (data == null || data == undefined) throw Error("data in create agent is undefined")
    return toAgent(res.data);
}

export async function updateAgent(agentId: string, payload: AgentUpdate): Promise<Agent> {
    const res = await updateAgentAgentsAgentIdPatch({ path: { agent_id: agentId }, body: toAgentUpdateDto(payload) });
    const data = res.data
    if (data == null || data == undefined) throw Error("data in update agent is undefined")
    return toAgent(res.data);
}

export async function deleteAgent(agentId: string): Promise<void> {
    await deleteAgentAgentsAgentIdDelete({ path: { agent_id: agentId } });
}

// ----- Chats -----
export async function listChats(agentId?: string | null): Promise<Chat[]> {
    const res = await listChatsChatsGet({ query: agentId ? { agent_id: agentId } : undefined });
    const data = res.data
    if (data == null || data == undefined) throw Error("data in create agent is undefined")
    return res.data.map(toChat);
}

export async function createChat(agentId: string): Promise<Chat> {
    const res = await createChatChatsPost({ body: { agent_id: agentId } });
    const data = res.data
    if (data == null || data == undefined) throw Error("data in create chat is undefined")
    return toChat(res.data);
}

export async function getChat(chatId: string): Promise<Chat> {
    const res = await getChatChatsChatIdGet({ path: { chat_id: chatId } });
    const data = res.data
    if (data == null || data == undefined) throw Error("data in chat is undefined")
    return toChat(res.data);
}

// ----- Messages -----
export async function listMessages(chatId: string): Promise<Message[]> {
    const res = await listMessagesMessagesByChatChatIdGet({ path: { chat_id: chatId } });
    const data = res.data
    if (!Array.isArray(data)) return []
    return data.map(toMessage);
}

export async function addMessage(payload: MessageCreate): Promise<Message> {
    const res = await addMessageMessagesPost({ body: toMessageCreateDto(payload) });
    const data = res.data
    if (data == null || data == undefined) throw Error("addmessage.data is empty")
    return toMessage(data);
}

// ----- Tools attached to agent (typed) -----
export async function listAgentTools(agentId: string): Promise<Tool[]> {
    const res = await listAgentToolsAgentsAgentIdToolsGet({ path: { agent_id: agentId } });
    const data = res.data
    if (!Array.isArray(data)) return [];
    return data.map(toTool);
}

export async function listTools(): Promise<Tool[]> {
    const res = await listToolsToolsGet();
    const data = res.data as unknown;
    if (!Array.isArray(data)) return []; // or throw
    return data.map((x) => toTool(x as any));
}

export async function getTool(toolId: string): Promise<Tool> {
    const res = await getToolToolsToolIdGet({ path: { tool_id: toolId } });
    return toTool(res.data as any);
}

export async function createTool(payload: ToolCreate): Promise<Tool> {
    const res = await createToolToolsPost({ body: toToolCreateDto(payload) });
    return toTool(res.data as any);
}

export async function updateTool(toolId: string, payload: ToolUpdate): Promise<Tool> {
    const res = await updateToolToolsToolIdPatch({ path: { tool_id: toolId }, body: toToolUpdateDto(payload) });
    return toTool(res.data as any);
}

export async function deleteTool(toolId: string): Promise<void> {
    await deleteToolToolsToolIdDelete({ path: { tool_id: toolId } });
}
