from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, Optional, Protocol, Set

from uuid import UUID

from cachetools import TTLCache

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from app.internal.store.store_client import AgentDTO, StoreClient
from app.internal.agents.middleware import Middleware

import elasticapm
from elasticapm import capture_span

def _stable_json(obj: Any) -> str:
    """Deterministic JSON encoding for cache keys."""
    return json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))


def _fingerprint(*parts: Any) -> str:
    """Hash multiple python objects into a stable cache key."""
    h = hashlib.sha256()
    for p in parts:
        h.update(_stable_json(p).encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()

class AgentRunnable(Protocol):
    async def ainvoke(self, message: str) -> str: ...

@dataclass(frozen=True)
class RuntimeConfig:
    agent_store_base_url: str
    mcp_url: str
    mcp_server_name: str = "agent-store"

_LLM_CACHE: TTLCache[str, Any] = TTLCache(maxsize=64, ttl=3600)  # 1 hour

def _build_llm(agent: AgentDTO) -> Any:
    """
    Interpret agent.model (your JSON field) and build the actual LLM.

    This version caches ChatOllama instances keyed by (provider, model, base_url, temperature).
    """
    cfg = agent.model or {}
    provider = (cfg.get("provider") or "ollama").lower()

    if provider != "ollama":
        raise RuntimeError(f"Unsupported provider '{provider}'")

    model = cfg.get("model") or "llama3.1:8b"

    base_url = "http://localhost:11434"

    temperature = cfg.get("temperature", None)
    temperature_f = float(temperature) if temperature is not None else None

    llm_key = _fingerprint(
        {"provider": provider, "model": model, "base_url": base_url, "temperature": temperature_f}
    )

    cached = _LLM_CACHE.get(llm_key)
    if cached is not None:
        elasticapm.label(llm_cache="hit")
        return cached

    elasticapm.label(llm_cache="miss")

    kwargs: Dict[str, Any] = {"model": model, "base_url": base_url}
    if temperature_f is not None:
        kwargs["temperature"] = temperature_f

    llm = ChatOllama(**kwargs)
    _LLM_CACHE[llm_key] = llm
    return llm


def _system_instruction(agent: AgentDTO) -> str:
    """
    Compose system instruction. Prefer explicit instruction in model config, else fall back to agent.role.
    """
    cfg = agent.model or {}
    return str(cfg.get("instruction") or agent.role or "You are a helpful assistant.")


def _context_tool_spec(agent: AgentDTO) -> Optional[Dict[str, Any]]:
    """
    Normalize your agent.context_tool JSON into:
      { "name": str, "args": dict, "prompt": str }
    """
    if not agent.context_tool:
        return None

    name = agent.context_tool.get("name")
    if not name:
        return None

    args = agent.context_tool.get("args") or {}
    if not isinstance(args, dict):
        args = {}

    prompt = agent.context_tool.get("prompt")
    return {"name": name, "args": args, "prompt": prompt}


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
                context = ""
            else:
                tool_result = await ctx_tool.ainvoke(self.ctx_args)
                context = tool_result if isinstance(tool_result, str) else str(tool_result)

        return await self.chain.ainvoke({"message": message, "context": context})

class ToolCallingRunnable:
    def __init__(
        self,
        llm: Any,
        mcp_client: MultiServerMCPClient,
        server_name: str,
        allowed_names: Set[str],
        system_prompt: str,
        middlewares: list[AgentMiddleware],
    ):
        self.llm = llm
        self.mcp_client = mcp_client
        self.server_name = server_name
        self.allowed_names = allowed_names
        self.system_prompt = system_prompt
        self._middlewares = middlewares

    async def ainvoke(self, message: str) -> str:
        async with self.mcp_client.session(self.server_name) as session:
            all_tools = await load_mcp_tools(session)
            tools = [t for t in all_tools if t.name in self.allowed_names]

            agent = create_agent(
                self.llm,
                tools,
                middleware=[self._middlewares[0]],
                system_prompt=self.system_prompt,
            )
            result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]})

            final_msg = result["messages"][-1]
            return final_msg.content

class AgentBuilder:
    def __init__(self, cfg: RuntimeConfig, store: StoreClient):
        self.cfg = cfg
        self.store = store

        self._runnable_cache: TTLCache[str, AgentRunnable] = TTLCache(maxsize=512, ttl=300)
        self._allowed_tools_cache: TTLCache[str, Set[str]] = TTLCache(maxsize=1024, ttl=60)

    async def _allowed_tool_names_cached(self, agent: AgentDTO) -> Set[str]:
        if agent.tools is not None:
            return {t.name for t in agent.tools}

        key = _fingerprint({"agent_id": str(agent.id)})
        cached = self._allowed_tools_cache.get(key)
        if cached is not None:
            elasticapm.label(allowed_tools_cache="hit")
            return cached

        elasticapm.label(allowed_tools_cache="miss")
        tools = await self.store.list_agent_tools(agent.id)
        names = {t.name for t in tools}
        self._allowed_tools_cache[key] = names
        return names

    def _runnable_cache_key(self, agent: AgentDTO, allowed_names: Set[str]) -> str:
        """
        Include everything that changes runnable wiring.
        If AgentDTO has updated_at/version, include it here for correctness.
        """
        ctx_spec = _context_tool_spec(agent)
        model_cfg = agent.model or {}

        return _fingerprint(
            {"agent_id": str(agent.id)},
            {"model": model_cfg},
            {"role": agent.role},
            {"ctx_spec": ctx_spec},
            {"allowed_names": sorted(allowed_names)},
            {"mcp_url": self.cfg.mcp_url, "server": self.cfg.mcp_server_name},
            # Optional invalidation hooks if you have them:
            # {"agent_updated_at": getattr(agent, "updated_at", None)},
        )

    async def build(self, agent: AgentDTO) -> AgentRunnable:
        elasticapm.set_custom_context({
            "agent_id": str(getattr(agent, "id", "")),
            "agent_name": getattr(agent, "name", None),
        })

        with capture_span("builder.build_llm", span_type="app", span_subtype="builder"):
            llm = _build_llm(agent)

        with capture_span("builder.system_instruction", span_type="app", span_subtype="builder"):
            sys = _system_instruction(agent)

        with capture_span("builder.allowed_tool_names", span_type="app", span_subtype="tools"):
            allowed_names = await self._allowed_tool_names_cached(agent)

        elasticapm.label(
            tools_allowed_count=len(allowed_names),
            tools_enabled=bool(allowed_names),
        )

        runnable_key = self._runnable_cache_key(agent, allowed_names)
        cached_runnable = self._runnable_cache.get(runnable_key)
        if cached_runnable is not None:
            elasticapm.label(runnable_cache="hit")
            return cached_runnable

        elasticapm.label(runnable_cache="miss")

        if not allowed_names:
            elasticapm.label(builder_mode="simple")
            with capture_span("builder.return_simple_runnable", span_type="app", span_subtype="runnable"):
                runnable = SimpleChatRunnable(llm, sys)
                self._runnable_cache[runnable_key] = runnable
                return runnable

        elasticapm.label(builder_mode="tools")

        with capture_span("builder.mcp_client_init", span_type="app", span_subtype="mcp"):
            mcp_client = MultiServerMCPClient({
                self.cfg.mcp_server_name: {"transport": "http", "url": self.cfg.mcp_url}
            })

        with capture_span("builder.context_tool_spec", span_type="app", span_subtype="tools"):
            ctx_spec = _context_tool_spec(agent)

        if ctx_spec is not None:
            elasticapm.label(builder_mode="context", ctx_tool_name=ctx_spec.get("name"))
            with capture_span("builder.return_context_runnable", span_type="app", span_subtype="runnable"):
                runnable = ContextChatRunnable(
                    llm=llm,
                    system_prompt=sys,
                    context_prompt=ctx_spec.get("prompt"),
                    mcp_client=mcp_client,
                    server_name=self.cfg.mcp_server_name,
                    allowed_names=allowed_names,
                    ctx_tool_name=ctx_spec["name"],
                    ctx_args=ctx_spec.get("args", {}),
                )
                self._runnable_cache[runnable_key] = runnable
                return runnable

        with capture_span("builder.middlewares_init", span_type="app", span_subtype="runnable"):
            middlewares = [Middleware()]

        elasticapm.label(builder_mode="toolcalling")

        with capture_span("builder.return_toolcalling_runnable", span_type="app", span_subtype="runnable"):
            runnable = ToolCallingRunnable(
                llm=llm,
                mcp_client=mcp_client,
                server_name=self.cfg.mcp_server_name,
                allowed_names=allowed_names,
                system_prompt=sys,
                middlewares=middlewares
            )
            self._runnable_cache[runnable_key] = runnable
            return runnable
