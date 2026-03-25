from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from datetime import datetime
from typing import Protocol

from agoffice_domain.errors import RoomAccessDeniedError, RoomNotFoundError
from agoffice_domain.schema import RoomConfig, RoomInfo, RoomListInfo, RoomUpdate, TunnelInfo
from agoffice_domain.room_mapping import RoomModel, room_model_to_info, room_models_to_list_info


class RoomRepository(Protocol):
    def new_room(self, user_id: str, room_config: RoomConfig) -> RoomModel: ...
    def update_room(self, room_id: str, updates: RoomUpdate) -> RoomModel: ...
    def get_room(self, room_id: str) -> RoomModel | None: ...
    def list_rooms(self, user_id: str, project_id: str) -> Sequence[RoomModel]: ...


class RoomRuntime(Protocol):
    async def run_room(self, room_id: str, project_id: str, user_id: str, token: str) -> RoomInfo: ...
    def get_pro_realtime_socketio_base_url(self, room_id: str) -> str: ...
    async def start_tunnel(self, room_id: str, tunnel_name: str, token: str) -> TunnelInfo: ...


class RoomEventBus(Protocol):
    def room_channel(self, room_id: str) -> str: ...
    async def publish(self, channel: str, message: str) -> None: ...
    async def subscribe(self, channel: str) -> AsyncGenerator[str, None]: ...


def get_owned_room(
    repository: RoomRepository,
    *,
    room_id: str,
    user_id: str,
) -> RoomModel:
    room = repository.get_room(room_id)
    if room is None:
        raise RoomNotFoundError(f"Room {room_id} not found")
    if room.user_id != user_id:
        raise RoomAccessDeniedError(f"Room {room_id} access denied")
    return room


def create_room(
    repository: RoomRepository,
    *,
    user_id: str,
    room_config: RoomConfig,
) -> RoomInfo:
    return room_model_to_info(repository.new_room(user_id=user_id, room_config=room_config))


async def open_room(
    repository: RoomRepository,
    runtime: RoomRuntime,
    *,
    room_id: str,
    user_id: str,
    token: str
) -> RoomInfo:
    room = get_owned_room(repository, room_id=room_id, user_id=user_id)
    await runtime.run_room(
        room_id=room.id,
        project_id=room.project_id,
        user_id=user_id,
        token=token,
    )
    updated = repository.update_room(
        room.id,
        RoomUpdate(task_started_at=datetime.now()),
    )
    return room_model_to_info(updated)


async def start_room_tunnel(
    repository: RoomRepository,
    runtime: RoomRuntime,
    *,
    room_id: str,
    user_id: str,
    token: str,
) -> TunnelInfo:
    get_owned_room(repository, room_id=room_id, user_id=user_id)
    return await runtime.start_tunnel(
        room_id=room_id,
        tunnel_name=room_id,
        token=token,
    )


def list_rooms(
    repository: RoomRepository,
    *,
    user_id: str,
    project_id: str,
) -> RoomListInfo:
    return room_models_to_list_info(repository.list_rooms(user_id, project_id))


async def apply_room_update(
    repository: RoomRepository,
    event_bus: RoomEventBus,
    *,
    room_id: str,
    updates: RoomUpdate,
) -> RoomInfo:
    updated = repository.update_room(room_id, updates)
    room_info = room_model_to_info(updated)
    await event_bus.publish(
        event_bus.room_channel(room_id),
        room_info.model_dump_json(),
    )
    return room_info


def get_owned_realtime_base_url(
    repository: RoomRepository,
    runtime: RoomRuntime,
    *,
    room_id: str,
    user_id: str,
) -> str:
    get_owned_room(repository, room_id=room_id, user_id=user_id)
    return runtime.get_pro_realtime_socketio_base_url(room_id)


async def subscribe_room_updates(
    repository: RoomRepository,
    event_bus: RoomEventBus,
    *,
    room_id: str,
    user_id: str,
) -> AsyncGenerator[str, None]:
    get_owned_room(repository, room_id=room_id, user_id=user_id)
    async for message in event_bus.subscribe(event_bus.room_channel(room_id)):
        yield message
