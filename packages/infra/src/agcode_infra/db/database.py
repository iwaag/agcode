from datetime import datetime
from sqlalchemy import Engine
from sqlmodel import SQLModel, Session, create_engine, select

from agcode_domain.schema import SessionConfig, SessionListInfo, SessionUpdate
from agcode_infra.config import get_database_settings
from agcode_infra.db.models import Agent, Instruction, Session as TaskSession

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_settings().url)
    return _engine


def init_database() -> None:
    SQLModel.metadata.create_all(get_engine())

def new_session(user_id: str, session_config: SessionConfig) -> TaskSession:
    new_session = TaskSession(title = session_config.title, user_id = user_id, project_id = session_config.project_id,
                              instruction = session_config.instruction, config = session_config.model_dump(),
                              created_at=datetime.now())
    with Session(get_engine()) as session:
        session.add(new_session)
        session.flush()
        session.commit()
        session.refresh(new_session)
        return new_session

def update_session(session_id: str, updates: SessionUpdate) -> TaskSession:
    with Session(get_engine()) as session:
        db_session = session.get(TaskSession, session_id)
        if not db_session:
            raise ValueError(f"Session {session_id} not found")
        update_data = updates.model_dump(exclude_unset=True)
        db_session.sqlmodel_update(update_data)
        db_session.updated_at = datetime.now()
        session.add(db_session)
        session.commit()
        session.refresh(db_session)
        return db_session

def get_session(session_id: str) -> TaskSession:
    with Session(get_engine()) as session:
        return session.get(TaskSession, session_id)

def list_sessions(user_id: str, project_id: str) -> SessionListInfo:
    with Session(get_engine()) as session:
        stmt = select(TaskSession).where(TaskSession.user_id == user_id, TaskSession.project_id == project_id)
        return session.exec(stmt).all()
