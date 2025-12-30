from fastapi import Depends, Request
from sqlmodel import Session
from chromadb import ClientAPI

from app.internal.store import db
from app.internal.store import db_vector

from app.internal.services.service_tools import ToolService
from app.internal.services.service_agents import AgentService
from app.internal.services.service_chats import ChatService
from app.internal.services.service_messages import MessageService
from app.internal.services.service_vectors import VectorService

from app.internal.store.repository_vectors import VectorRepository


def get_session():
    with Session(db.engine) as s:
        yield s

def get_vector_client(request: Request) -> ClientAPI:
    """
    Tries to get the vector client from app state; falls back to default client.
    """
    client = getattr(request.app.state, "vector_client", None)
    return client or db_vector.get_client()

def get_vector_repository(
    client: ClientAPI = Depends(get_vector_client),
) -> VectorRepository:
    """
    Creates a VectorRepository instance.
    
    :param client: The client of the vector database
    :type client: ClientAPI
    :return: The repository for vector operations
    :rtype: VectorRepository
    """
    return VectorRepository(client)

def get_vector_service(
    repo: VectorRepository = Depends(get_vector_repository),
) -> VectorService:
    """
    Creates a VectorService instance.
    
    :param repo: The repository for vector operations
    :type repo: VectorRepository
    :return: A service for vector operations
    :rtype: VectorService
    """
    return VectorService(repo)

def get_tool_service(
    request: Request,
    session: Session = Depends(get_session),
) -> ToolService:
    sync = getattr(request.app.state, "tool_engine", None)
    return ToolService(session, sync=sync)

def get_agent_service(
        session: Session = Depends(get_session)
) -> AgentService:
    return AgentService(session)

def get_message_service(
        session: Session = Depends(get_session)
) -> MessageService:
    return MessageService(session)

def get_chat_service(
        session: Session = Depends(get_session)
) -> ChatService:
    return ChatService(session)