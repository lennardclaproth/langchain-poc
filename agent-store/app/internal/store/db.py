# app/db.py
from typing import Generator

from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///agent_store.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency.
    Creates one Session per request and closes it afterwards.
    """
    with Session(engine) as session:
        yield session
