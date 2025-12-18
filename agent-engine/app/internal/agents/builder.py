from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Set

from uuid import UUID

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langchain.agents import create_agent

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from app.internal.store.store_client import AgentDTO, StoreClient


# ---------- Runnable protocol ----------
class AgentRunnable(Protocol):
    async def ainvoke(self, message: str) -> str: ...


# ---------- Builder config ----------
@dataclass(frozen=True)
class RuntimeConfig:
    agent_store_base_url: str
    mcp_url: str
    mcp_server_name: str = "agent-store"

# ---------- LLM factory ----------
def _build_llm(agent: AgentDTO) -> Any:
    """
    Interpret agent.model (your JSON field) and build the actual LLM.

    Example expected:
      agent.model = {
        "provider": "ollama",
        "model": "llama3.1:8b",
        "base_url": "http://192.168.178.42:11434",
        "temperature": 0.2
      }
    """
    cfg = agent.model or {}
    provider = (cfg.get("provider") or "ollama").lower()

    if provider != "ollama":
        raise RuntimeError(f"Unsupported provider '{provider}'")

    model = cfg.get("model") or "llama3.1:8b"
    base_url = "http://192.168.178.42:11434"
    # temperature = cfg.get("temperature", None)

    kwargs: Dict[str, Any] = {"model": model, "base_url": base_url}
    # if temperature is not None:
    #     kwargs["temperature"] = float(temperature)

    return ChatOllama(**kwargs)


def _system_instruction(agent: AgentDTO) -> str:
    """
    Compose system instruction. Prefer explicit instruction in model config, else fall back to agent.role.
    """
    cfg = agent.model or {}
    return str(cfg.get("instruction") or agent.role or "You are a helpful assistant.")


# ---------- Context tool spec ----------
def _context_tool_spec(agent: AgentDTO) -> Optional[Dict[str, Any]]:
    """
    Normalize your agent.context_tool JSON into:
      { "name": str, "args": dict, "prompt": str }

    If your schema differs, change only this function.
    """
    if not agent.context_tool:
        return None

    name = agent.context_tool.get("name")
    if not name:
        return None

    args = agent.context_tool.get("args") or {}
    if not isinstance(args, dict):
        args = {}

    # Optional override prompt; otherwise compose from system instruction.
    prompt = agent.context_tool.get("prompt")
    return {"name": name, "args": args, "prompt": prompt}


# ---------- Concrete runnables ----------
class SimpleChatRunnable:
    def __init__(self, llm: Any, system_prompt: str):
        self.chain = (
            ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{message}"),
            ])
            | llm
            | StrOutputParser()
        )

    async def ainvoke(self, message: str) -> str:
        return await self.chain.ainvoke({"message": message})


class ContextChatRunnable:
    def __init__(
        self,
        llm: Any,
        system_prompt: str,
        context_prompt: Optional[str],
        mcp_client: MultiServerMCPClient,
        server_name: str,
        allowed_names: Set[str],
        ctx_tool_name: str,
        ctx_args: Dict[str, Any],
    ):
        sys = context_prompt or (
            f"{system_prompt}\n\nAnswer using the provided context. "
            f"If context is empty/invalid, say you don't know."
        )

        self.llm = llm
        self.sys = sys
        self.mcp_client = mcp_client
        self.server_name = server_name
        self.allowed_names = allowed_names
        self.ctx_tool_name = ctx_tool_name
        self.ctx_args = ctx_args

        self.chain = (
            ChatPromptTemplate.from_messages([
                ("system", sys),
                ("human", "Question: {message}\n\nContext:\n{context}"),
            ])
            | llm
            | StrOutputParser()
        )

    async def ainvoke(self, message: str) -> str:
        async with self.mcp_client.session(self.server_name) as session:
            all_tools = await load_mcp_tools(session)
            tools = [t for t in all_tools if t.name in self.allowed_names]

            ctx_tool = next((t for t in tools if t.name == self.ctx_tool_name), None)
            if ctx_tool is None:
                # degrade gracefully
                context = ""
            else:
                tool_result = await ctx_tool.ainvoke(self.ctx_args)
                context = tool_result if isinstance(tool_result, str) else str(tool_result)

        return await self.chain.ainvoke({"message": message, "context": context})


class ToolCallingRunnable:
    def __init__(self, llm: Any, mcp_client: MultiServerMCPClient, server_name: str, allowed_names: Set[str], system_prompt: str):
        self.llm = llm
        self.mcp_client = mcp_client
        self.server_name = server_name
        self.allowed_names = allowed_names
        self.system_prompt = system_prompt

    async def ainvoke(self, message: str) -> str:
        async with self.mcp_client.session(self.server_name) as session:
            all_tools = await load_mcp_tools(session)
            tools = [t for t in all_tools if t.name in self.allowed_names]

            agent = create_agent(self.llm, tools, system_prompt=self.system_prompt)
            result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]})

            # Return the final assistant message (string), like your working endpoint does
            final_msg = result["messages"][-1]
            return final_msg.content

async def _allowed_tool_names(cfg: RuntimeConfig, store: StoreClient, agent: AgentDTO) -> Set[str]:
    if agent.tools is not None:
        return {t.name for t in agent.tools}
    tools = await store.list_agent_tools(agent.id)
    return {t.name for t in tools}

# ---------- The Builder itself ----------
class AgentBuilder:
    def __init__(self, cfg: RuntimeConfig, store: StoreClient):
        self.cfg = cfg
        self.store = store

    async def build(self, agent: AgentDTO) -> AgentRunnable:
        llm = _build_llm(agent)
        sys = _system_instruction(agent)

        allowed_names = await _allowed_tool_names(self.cfg, self.store, agent)

        # If there are no tools at all, we can immediately fall back
        if not allowed_names:
            return SimpleChatRunnable(llm, sys)

        # Create a client once and pass it into runnables that will open sessions per-call
        mcp_client = MultiServerMCPClient({
            self.cfg.mcp_server_name: {"transport": "http", "url": self.cfg.mcp_url}
        })

        # Decision logic: context_tool > tools > simple
        ctx_spec = _context_tool_spec(agent)
        if ctx_spec is not None:
            return ContextChatRunnable(
                llm=llm,
                system_prompt=sys,
                context_prompt=ctx_spec.get("prompt"),
                mcp_client=mcp_client,
                server_name=self.cfg.mcp_server_name,
                allowed_names=allowed_names,
                ctx_tool_name=ctx_spec["name"],
                ctx_args=ctx_spec.get("args", {}),
            )

        return ToolCallingRunnable(
            llm=llm,
            mcp_client=mcp_client,
            server_name=self.cfg.mcp_server_name,
            allowed_names=allowed_names,
            system_prompt=sys,
        )