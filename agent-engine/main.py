import asyncio
from fastapi import FastAPI
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import uvicorn

llm = ChatOllama(model="llama3.1:8b", base_url="http://192.168.178.42:11434")

client = MultiServerMCPClient({
    "agent-store": {"transport": "http", "url": "http://localhost:8000/mcp"}
})

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer using the context. If context is empty/invalid, say you don't know."),
    ("human", "Question: {question}\n\nContext:\n{context}")
])

async def main():
    question = "What is the weather in New York City?"

    async with client.session("agent-store") as session:
        tools = await load_mcp_tools(session)

        # find the tool by name
        weather_tool = next(t for t in tools if t.name == "get_weather")

        # "retrieve" context by calling the tool (live retrieval)
        tool_result = await weather_tool.ainvoke({"location": "New York City"})

        # tool_result may be str or structured; make it text
        context = tool_result if isinstance(tool_result, str) else str(tool_result)

        chain = prompt | llm | StrOutputParser()
        answer = await chain.ainvoke({"question": question, "context": context})
        print(answer)

app = FastAPI(title="agent-store")

@app.get("/api/chat")
async def chat(message: str):
    async with client.session("agent-store") as session:
        tools = await load_mcp_tools(session)

        # find the tool by name
        weather_tool = next(t for t in tools if t.name == "get_weather")

        # "retrieve" context by calling the tool (live retrieval)
        tool_result = await weather_tool.ainvoke({"location": "New York City"})

        # tool_result may be str or structured; make it text
        context = tool_result if isinstance(tool_result, str) else str(tool_result)

        chain = prompt | llm | StrOutputParser()
        answer = await chain.ainvoke({"question": message, "context": context})

    return answer

def run():
    uvicorn.run(
        "main:app",
        host = "127.0.0.1",
        port = 8001,
        reload = True
    )

if __name__ == "__main__":
    # asyncio.run(main())
    run()
