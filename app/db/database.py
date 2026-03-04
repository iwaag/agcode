from datetime import datetime
import os
from typing import List
from sqlalchemy import Engine
from sqlmodel import SQLModel, Session, create_engine, select

from schema.schema import SessionConfig, SessionListInfo, SessionUpdate
from models.models import Agent, Instruction, Session as TaskSession



SQL_TYPE = os.getenv("SQL_TYPE")
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
SQL_HOST = os.getenv("SQL_HOST")
SQL_PORT = os.getenv("SQL_PORT")
SQL_DB = os.getenv("SQL_DB")
sql_url = f"{SQL_TYPE}://{SQL_USER}:{SQL_PASSWORD}@{SQL_HOST}:{SQL_PORT}/{SQL_DB}"
engine = create_engine(sql_url)
SQLModel.metadata.create_all(engine)

def new_session(user_id: str, session_config: SessionConfig) -> TaskSession:
    new_session = TaskSession(title = session_config.title, user_id = user_id, project_id = session_config.project_id,
                              instruction = session_config.instruction, config = session_config.model_dump(),
                              created_at=datetime.now())
    with Session(engine) as session:
        session.add(new_session)
        session.flush()
        session.commit()
        session.refresh(new_session)
        return new_session

def update_session(session_id: str, updates: SessionUpdate) -> TaskSession:
    with Session(engine) as session:
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
    with Session(engine) as session:
        return session.get(TaskSession, session_id)

def list_sessions(user_id: str, project_id: str) -> SessionListInfo:
    with Session(engine) as session:
        stmt = select(TaskSession).where(TaskSession.user_id == user_id, TaskSession.project_id == project_id)
        return session.exec(stmt).all()