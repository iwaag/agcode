from typing import List

from pydantic import BaseModel, AnyHttpUrl

class AgentDeployment(BaseModel):
    agent_id: str
    instruction: str

class SessionConfig(BaseModel):
    agent_deployments: List[AgentDeployment]
    project_id: str
    instruction: str

class AgentConfig(BaseModel):
    name: str
    model: str


class SessionInfo(BaseModel):
    session_id: str

