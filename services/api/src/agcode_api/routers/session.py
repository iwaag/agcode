from fastapi import APIRouter, Depends, HTTPException
from agpyutils.auth import get_auth_info, AuthInfo
import httpx
from sse_starlette.sse import EventSourceResponse

from agcode_domain import session_service
from agcode_domain.errors import SessionAccessDeniedError, SessionNotFoundError
from agcode_domain.schema import (
    NoobTaskAcceptedResponse,
    NoobTaskEvents,
    NoobTaskRequest,
    NoobTaskResult,
    NoobTaskStatus,
    SessionConfig,
    SessionInfo,
    SessionListInfo,
    SessionUpdate,
    TunnelInfo,
)
from agcode_infra.db import database as db
from agcode_infra.orchestration import session_k8s as task_session
from agcode_infra.pubsub import redis as redis_service

router = APIRouter()


def _raise_http_session_error(exc: Exception) -> None:
    if isinstance(exc, SessionNotFoundError):
        raise HTTPException(status_code=404, detail="Session not found")
    if isinstance(exc, SessionAccessDeniedError):
        raise HTTPException(status_code=403, detail="Session access denied")
    raise exc


@router.post("/new", summary="New task session")
async def new_session(session: SessionConfig,  auth: AuthInfo = Depends(get_auth_info)) -> SessionInfo:
    return session_service.create_session(
        db,
        user_id=auth.user_id,
        session_config=session,
    )

@router.post("/open", summary="Open task session.")
async def open_session(session_id: str,  auth: AuthInfo = Depends(get_auth_info)) -> SessionInfo:
    try:
        return await session_service.open_session(
            db,
            task_session,
            session_id=session_id,
            user_id=auth.user_id,
            token=auth.token,
        )
    except (SessionNotFoundError, SessionAccessDeniedError) as exc:
        _raise_http_session_error(exc)


@router.get("/list", summary="Task session list")
async def task_list(project_id: str, auth: AuthInfo = Depends(get_auth_info)) -> SessionListInfo:
    return session_service.list_sessions(
        db,
        user_id=auth.user_id,
        project_id=project_id,
    )


@router.post("/hook/{session_id}", summary="Webhook to receive session updates from workers")
async def hook_on_update(session_id: str, updates: SessionUpdate) -> SessionInfo:
    return await session_service.apply_session_update(
        db,
        redis_service,
        session_id=session_id,
        updates=updates,
    )


@router.get("/stream/{session_id}", summary="SSE stream for real-time session updates")
async def stream_session(session_id: str, auth: AuthInfo = Depends(get_auth_info)):
    async def event_generator():
        try:
            async for message in session_service.subscribe_session_updates(
                db,
                redis_service,
                session_id=session_id,
                user_id=auth.user_id,
            ):
                yield {"data": message}
        except (SessionNotFoundError, SessionAccessDeniedError) as exc:
            _raise_http_session_error(exc)

    return EventSourceResponse(event_generator())


@router.post("/{session_id}/tunnel/start", summary="Start VS Code tunnel for a session")
async def start_session_tunnel(session_id: str, auth: AuthInfo = Depends(get_auth_info)) -> TunnelInfo:
    try:
        return await session_service.start_session_tunnel(
            db,
            task_session,
            session_id=session_id,
            user_id=auth.user_id,
            token=auth.token,
        )
    except (SessionNotFoundError, SessionAccessDeniedError) as exc:
        _raise_http_session_error(exc)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Tunnel worker request timed out") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Tunnel worker request failed: {exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Tunnel worker is unreachable") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{session_id}/noob/request", summary="Submit a NOOB worker request")
async def submit_noob_request(
    session_id: str,
    request: NoobTaskRequest,
    auth: AuthInfo = Depends(get_auth_info),
) -> NoobTaskAcceptedResponse:
    try:
        session = session_service.get_owned_session(
            db,
            session_id=session_id,
            user_id=auth.user_id,
        )
        await task_session.submit_noob_task(
            session_id=session.id,
            user_id=auth.user_id,
            token=auth.token,
            request=request,
        )
        return NoobTaskAcceptedResponse(status="accepted")
    except (SessionNotFoundError, SessionAccessDeniedError) as exc:
        _raise_http_session_error(exc)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{session_id}/noob/status", summary="Get NOOB worker status")
async def get_noob_status(session_id: str, auth: AuthInfo = Depends(get_auth_info)) -> NoobTaskStatus:
    try:
        session = session_service.get_owned_session(
            db,
            session_id=session_id,
            user_id=auth.user_id,
        )
        return await task_session.get_noob_task_status(session.id)
    except (SessionNotFoundError, SessionAccessDeniedError) as exc:
        _raise_http_session_error(exc)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{session_id}/noob/result", summary="Get NOOB worker result")
async def get_noob_result(session_id: str, auth: AuthInfo = Depends(get_auth_info)) -> NoobTaskResult:
    try:
        session = session_service.get_owned_session(
            db,
            session_id=session_id,
            user_id=auth.user_id,
        )
        return await task_session.get_noob_task_result(session.id)
    except (SessionNotFoundError, SessionAccessDeniedError) as exc:
        _raise_http_session_error(exc)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{session_id}/noob/events", summary="Get NOOB worker events")
async def get_noob_events(
    session_id: str,
    tail: int = 200,
    auth: AuthInfo = Depends(get_auth_info),
) -> NoobTaskEvents:
    try:
        session = session_service.get_owned_session(
            db,
            session_id=session_id,
            user_id=auth.user_id,
        )
        return await task_session.get_noob_task_events(session.id, tail=tail)
    except (SessionNotFoundError, SessionAccessDeniedError) as exc:
        _raise_http_session_error(exc)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
