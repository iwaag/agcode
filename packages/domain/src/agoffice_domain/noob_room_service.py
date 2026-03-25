from __future__ import annotations

from agoffice_domain.errors import NoobRoomConflictError, NoobThreadNotFoundError, RoomAccessDeniedError, RoomNotFoundError
from agoffice_domain.schema import (
    NoobRoomCreateRequest,
    NoobRoomInfo,
    NoobWorkspacePrepSpec,
    NoobWorkspacePrepRequest,
    NoobThreadCreateRequest,
    NoobThreadInfo,
    NoobThreadRequest,
    NoobTaskRequest,
)


def _to_noob_room_info(model: object) -> NoobRoomInfo:
    return NoobRoomInfo(
        id=getattr(model, "id"),
        user_id=getattr(model, "user_id"),
        project_id=getattr(model, "project_id"),
        title=getattr(model, "title"),
        initial_instruction=getattr(model, "initial_instruction"),
        created_at=getattr(model, "created_at"),
        updated_at=getattr(model, "updated_at"),
        finished_at=getattr(model, "finished_at"),
        config=getattr(model, "config"),
    )


def _to_noob_thread_info(model: object) -> NoobThreadInfo:
    return NoobThreadInfo(
        id=getattr(model, "id"),
        noob_room_id=getattr(model, "noob_room_id"),
        title=getattr(model, "title"),
        keep_context=getattr(model, "keep_context"),
        status=getattr(model, "status"),
        created_at=getattr(model, "created_at"),
        updated_at=getattr(model, "updated_at"),
    )


def create_noob_room(repository: object, *, user_id: str, request: NoobRoomCreateRequest) -> NoobRoomInfo:
    active = repository.get_active_noob_room_for_user(user_id)
    if active is not None:
        raise NoobRoomConflictError(f"User {user_id} already has an active NOOB room: {active.id}")
    return _to_noob_room_info(repository.new_noob_room(user_id=user_id, room_config=request))


def get_owned_noob_room(repository: object, *, room_id: str, user_id: str) -> object:
    room = repository.get_noob_room(room_id)
    if room is None:
        raise RoomNotFoundError(f"NOOB room {room_id} not found")
    if room.user_id != user_id:
        raise RoomAccessDeniedError(f"NOOB room {room_id} access denied")
    return room


def create_or_get_thread(
    repository: object,
    *,
    noob_room_id: str,
    user_id: str,
    request: NoobThreadCreateRequest,
) -> NoobThreadInfo:
    get_owned_noob_room(repository, room_id=noob_room_id, user_id=user_id)
    existing = repository.get_active_noob_thread(noob_room_id)
    if existing is not None:
        return _to_noob_thread_info(existing)
    return _to_noob_thread_info(repository.create_noob_thread(noob_room_id, request))


def get_owned_noob_thread(repository: object, *, noob_room_id: str, thread_id: str, user_id: str) -> object:
    get_owned_noob_room(repository, room_id=noob_room_id, user_id=user_id)
    thread = repository.get_noob_thread(thread_id)
    if thread is None or thread.noob_room_id != noob_room_id:
        raise NoobThreadNotFoundError(f"NOOB thread {thread_id} not found")
    return thread


def build_thread_task_request(thread: object, request: NoobThreadRequest) -> NoobTaskRequest:
    return NoobTaskRequest(
        instruction=request.instruction,
        context_file_paths=request.context_file_paths,
        workspace_path=request.workspace_path or "workspace",
        output_file_path=request.output_file_path,
        system_prompt=request.system_prompt,
        model=request.model,
        thread_id=getattr(thread, "id"),
    )


def resolve_prep_request(
    repository: object,
    *,
    noob_room_id: str,
    user_id: str,
    request: NoobWorkspacePrepRequest | None,
) -> NoobWorkspacePrepRequest:
    room = get_owned_noob_room(repository, room_id=noob_room_id, user_id=user_id)
    if request is not None:
        return request

    config = getattr(room, "config", {}) or {}
    prep = config.get("prep")
    if isinstance(prep, dict):
        return NoobWorkspacePrepRequest(spec=NoobWorkspacePrepSpec.model_validate(prep))
    raise ValueError(f"NOOB room {noob_room_id} does not have a stored prep spec")
