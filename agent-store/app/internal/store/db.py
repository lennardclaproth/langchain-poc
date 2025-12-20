# app/db.py
from typing import Generator, Optional
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.engine import Engine

DATABASE_URL = "sqlite:///agent_store.db"

engine: Engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

def set_engine(new_engine: Engine) -> None:
    global engine
    engine = new_engine

def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
