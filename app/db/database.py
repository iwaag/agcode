from datetime import datetime
import os
from typing import List
from sqlalchemy import Engine
from sqlmodel import SQLModel, Session, create_engine, select

from schema.schema import SessionConfig
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

def new_session(user_id: str, project_id: str, instruction: str, session_config: SessionConfig) -> TaskSession:
    new_session = TaskSession(title = "untitled session", user_id = user_id, project_id = project_id,
                              instruction_id = instruction, config = session_config.model_dump(),
                              data_created_at = datetime.now())
    with Session(engine) as session:
        session = session.add(new_session)
        session.flush()
        session.commit()
        session.refresh(new_session)
        return new_session

def list_sessions(user_id: str, project_id: str) -> List[TaskSession]:
    with Session(engine) as session:
        stmt = select(TaskSession).where(TaskSession.user_id == user_id, TaskSession.project_id == project_id)
        return session.exec(stmt).all()