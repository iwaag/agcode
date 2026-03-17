from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from pydantic import BaseModel, AnyHttpUrl

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
