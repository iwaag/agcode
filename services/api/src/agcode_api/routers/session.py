from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from agpyutils.auth import get_auth_info, AuthInfo
from sse_starlette.sse import EventSourceResponse

from agcode_domain.schema import SessionConfig, SessionInfo, SessionListInfo, SessionUpdate
from agcode_domain import session_mapping as common
from agcode_infra.db import database as db
from agcode_infra.orchestration import session_k8s as task_session
from agcode_infra.pubsub import redis as redis_service

router = APIRouter()


def _get_owned_session(session_id: str, user_id: str):
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Session access denied")
    return session


@router.post("/new", summary="New task session")
async def new_session(session: SessionConfig,  auth: AuthInfo = Depends(get_auth_info)) -> SessionInfo:
    new_session_model = db.new_session(user_id=auth.user_id, session_config=session)
    #new_session = await task_session.new_session(session=session, task_id=new_session_data.id, project_id=session.project_id, user_id=auth.user_id)
    new_session_info = common.session_model_to_scheme(new_session_model)
    return new_session_info

@router.post("/open", summary="Open task session.")
async def open_session(session_id: str,  auth: AuthInfo = Depends(get_auth_info)) -> SessionInfo:
    session_data = _get_owned_session(session_id=session_id, user_id=auth.user_id)
    await task_session.run_session(session_id=session_data.id, project_id=session_data.project_id, user_id=auth.user_id)
    new_session_model = db.update_session(session_data.id, SessionUpdate(task_started_at=datetime.now()))
    new_session_info = common.session_model_to_scheme(new_session_model)
    return new_session_info


@router.get("/list", summary="Task session list")
async def task_list(project_id: str, auth: AuthInfo = Depends(get_auth_info)) -> SessionListInfo:
    session_sequence = db.list_sessions(auth.user_id, project_id)
    session_info_list = common.session_model_sequence_to_sceme(session_sequence)
    return session_info_list


@router.post("/hook/{session_id}", summary="Webhook to receive session updates from workers")
async def hook_on_update(session_id: str, updates: SessionUpdate):
    updated = db.update_session(session_id, updates)
    channel = redis_service.session_channel(session_id)
    await redis_service.publish(channel, updated.mode)
    return updated


@router.get("/stream/{session_id}", summary="SSE stream for real-time session updates")
async def stream_session(session_id: str, auth: AuthInfo = Depends(get_auth_info)):
    _get_owned_session(session_id=session_id, user_id=auth.user_id)

    async def event_generator():
        async for message in redis_service.subscribe(redis_service.session_channel(session_id)):
            yield {"data": message}

    return EventSourceResponse(event_generator())
