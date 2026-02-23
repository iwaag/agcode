from fastapi import APIRouter, Depends, Header
from agpyutils.auth import get_auth_info, AuthInfo
from schema.schema import SessionConfig, SessionInfo
import db.database as db
import service.session_k8s as task_session

router = APIRouter()

@router.post("/new", summary="New task session")
async def new_session(session: SessionConfig, project_id: str, auth: AuthInfo = Depends(get_auth_info)) -> SessionInfo:
    new_session_data = db.new_session(auth.user_id, project_id, session)
    new_session = await task_session.new_session(session=session, task_id=new_session_data.id, project_id=project_id, user_id=auth.user_id)
    return new_session

@router.get("/list", summary="task session list")
async def task_list(project_id: str, auth: AuthInfo = Depends(get_auth_info)) -> SessionInfo:
    return SessionInfo()

@router.post("/hook", summary="webhook to receive session updates")
async def hook_on_update(info: SessionInfo, auth: AuthInfo = Depends(get_auth_info)) -> SessionInfo:
    return SessionInfo()
