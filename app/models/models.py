from datetime import datetime
from typing import Any, Optional
import nanoid

from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSONB
from uuid import UUID as PyUUID
from sqlmodel import Field, Column, SQLModel, String

def generate_nanoid() -> str:
    return nanoid.generate(size=12)

class Agent(SQLModel, table=True):
    id: str = Field(
        default_factory=generate_nanoid,
        sa_column=Column(String(12), primary_key=True, index=True, nullable=False),
    )
    name: str
    model: str

class Instruction(SQLModel, table=True):
    id: str = Field(
        default_factory=generate_nanoid,
        sa_column=Column(String(12), primary_key=True, index=True, nullable=False),
    )
    title: str
    content: str

class Session(SQLModel, table=True):
    id: str = Field(
        default_factory=generate_nanoid,
        sa_column=Column(String(12), primary_key=True, index=True, nullable=False),
    )
    title: str
    instruction: str
    created_at: datetime
    task_started_at: Optional[datetime]
    finished_at: Optional[datetime] = None
    updated_at: Optional[datetime]
    user_id: str
    project_id: str
    instruction_id: str
    config: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(MutableDict.as_mutable(JSONB), nullable=False),
    )