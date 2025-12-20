import asyncio
from fastapi import FastAPI
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .api.middlewares.global_exception_handler import GlobalExceptionHandler
from .api.middlewares.request_timing import RequestTimingMiddleware
from langchain.agents import create_agent
from .logging_config import setup_logging
from .api.routers import chats

import uvicorn

setup_logging()

llm = ChatOllama(model="llama3.1:8b", base_url="http://192.168.178.42:11434")

client = MultiServerMCPClient({
    "agent-store": {"transport": "http", "url": "http://localhost:8000/mcp"}
})

prompt_with_context = ChatPromptTemplate.from_messages([
    ("system", "Answer using the context. If context is empty/invalid, say you don't know."),
    ("human", "Question: {question}\n\nContext:\n{context}")
])

# Example prompt that supports tool calling
prompt_with_tools = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Use tools when useful."),
    ("human", "{question}"),
])

app = FastAPI(title="agent-engine")
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(
    GlobalExceptionHandler,
    include_traceback=False,
    instance_base_url=None,
    error_header_name="X-Error-Id",
)
app.include_router(chats.router, prefix="/api")

@app.get("/api/chat-with-context")
async def chat(message: str):
    async with client.session("agent-store") as session:
        tools = await load_mcp_tools(session)

        # find the tool by name
        weather_tool = next(t for t in tools if t.name == "get_weather")

        # "retrieve" context by calling the tool (live retrieval)
        tool_result = await weather_tool.ainvoke({"location": "New York City"})

        # tool_result may be str or structured; make it text
        context = tool_result if isinstance(tool_result, str) else str(tool_result)

        chain = prompt_with_context | llm | StrOutputParser()
        answer = await chain.ainvoke({"question": message, "context": context})

    return answer

@app.get("/api/chat-with-tools")
async def chat_with_tools(message: str):
    async with client.session("agent-store") as session:
        tools = await load_mcp_tools(session)

        # create_agent is NOT async, and it needs model + tools
        agent = create_agent(llm, tools, system_prompt="You are a helpful assistant. Use tools when useful.")

        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": message}]
        })

        # Agent returns a state; typically the final assistant message is last
        final_msg = result["messages"][-1]
        return final_msg.content

def run():
    uvicorn.run(
        "app.main:app",
        host = "127.0.0.1",
        port = 8001,
        reload = True,
        access_log=False,
    )

if __name__ == "__main__":
    # asyncio.run(main())
    run()
