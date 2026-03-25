from typing import Protocol, Sequence

from agoffice_domain.schema import RoomInfo, RoomListInfo


class RoomModel(Protocol):
    id: str
    user_id: str
    project_id: str
    title: str
    task_started_at: object
    finished_at: object
    config: dict


def room_model_to_info(model: RoomModel) -> RoomInfo:
    return RoomInfo(id=model.id, title=model.title, task_started_at=model.task_started_at, finished_at=model.finished_at, config=model.config)


def room_models_to_list_info(room_squence: Sequence[RoomModel]) -> RoomListInfo:
    return RoomListInfo(rooms=[room_model_to_info(room) for room in room_squence])
