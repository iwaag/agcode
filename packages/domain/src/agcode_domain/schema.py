from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from pydantic import BaseModel, Field

class AgentDeployment(BaseModel):
    agent_id: str
    instruction: str

class SessionConfig(BaseModel):
    agent_deployments: List[AgentDeployment]
    title: str
    project_id: str
    instruction: str

class AgentConfig(BaseModel):
    name: str
    model: str

class SessionUpdate(BaseModel):
    title: Optional[str] = None
    task_started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    config: Optional[Dict[str, Any]] = None

class SessionInfo(SessionUpdate):
    id: str

class SessionListInfo(BaseModel):
    sessions: Sequence[SessionInfo]


class TunnelInfo(BaseModel):
    tunnel_name: str


class NoobTaskRequest(BaseModel):
    instruction: str = Field(min_length=1)
    context_file_paths: List[str] = Field(default_factory=list)
    workspace_path: Optional[str] = None
    output_file_path: str = "artifacts/response.md"
    system_prompt: Optional[str] = None
    model: Optional[str] = None


class NoobTaskAcceptedResponse(BaseModel):
    status: str


class NoobTaskStatus(BaseModel):
    status: str
    updated_at: Optional[datetime] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None


class NoobTaskResult(BaseModel):
    exit_code: Optional[int] = None
    completed_at: Optional[datetime] = None
    output_path: Optional[str] = None
    content: Optional[str] = None
    stdout_path: Optional[str] = None
    stderr_path: Optional[str] = None
    error: Optional[str] = None


class NoobTaskEvent(BaseModel):
    timestamp: datetime
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class NoobTaskEvents(BaseModel):
    events: List[NoobTaskEvent]
