from datetime import datetime
from sqlalchemy import Engine
from sqlmodel import SQLModel, Session, create_engine, select

from agoffice_domain.schema import (
    NoobRoomCreateRequest,
    NoobRoomUpdate,
    NoobThreadCreateRequest,
    RoomConfig,
    RoomUpdate,
)
from agoffice_infra.config import get_database_settings
from agoffice_infra.db.models import (
    Agent,
    Instruction,
    NoobRoom,
    NoobThread,
    Room as TaskRoom,
    generate_room_id,
)

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_settings().url)
    return _engine


def init_database() -> None:
    SQLModel.metadata.create_all(get_engine())


def _allocate_room_index(session: Session, *, user_id: str, project_id: str) -> int:
    stmt = select(TaskRoom.room_index).where(
        TaskRoom.user_id == user_id,
        TaskRoom.project_id == project_id,
    )
    used_indexes = set(session.exec(stmt).all())
    for room_index in range(101):
        if room_index not in used_indexes:
            return room_index
    raise ValueError(f"No available room index for user_id={user_id} project_id={project_id}")



def new_room(user_id: str, room_config: RoomConfig) -> TaskRoom:
    with Session(get_engine()) as session:
        room_index = _allocate_room_index(session, user_id=user_id, project_id=room_config.project_id)
        new_room = TaskRoom(
            id=generate_room_id(
                user_id=user_id,
                project_id=room_config.project_id,
                room_index=room_index,
            ),
            title=room_config.title,
            user_id=user_id,
            project_id=room_config.project_id,
            room_index=room_index,
            instruction=room_config.instruction,
            config=room_config.model_dump(),
            created_at=datetime.now(),
        )
        session.add(new_room)
        session.flush()
        session.commit()
        session.refresh(new_room)
        return new_room

def update_room(room_id: str, updates: RoomUpdate) -> TaskRoom:
    with Session(get_engine()) as session:
        db_room = session.get(TaskRoom, room_id)
        if not db_room:
            raise ValueError(f"Room {room_id} not found")
        update_data = updates.model_dump(exclude_unset=True)
        db_room.sqlmodel_update(update_data)
        db_room.updated_at = datetime.now()
        session.add(db_room)
        session.commit()
        session.refresh(db_room)
        return db_room

def get_room(room_id: str) -> TaskRoom:
    with Session(get_engine()) as session:
        return session.get(TaskRoom, room_id)


def get_noob_room(room_id: str) -> NoobRoom | None:
    with Session(get_engine()) as session:
        return session.get(NoobRoom, room_id)


def get_active_noob_room_for_user(user_id: str) -> NoobRoom | None:
    with Session(get_engine()) as session:
        stmt = (
            select(NoobRoom)
            .where(NoobRoom.user_id == user_id, NoobRoom.finished_at.is_(None))
            .order_by(NoobRoom.created_at.desc())
        )
        return session.exec(stmt).first()


def new_noob_room(user_id: str, room_config: NoobRoomCreateRequest) -> NoobRoom:
    new_room = NoobRoom(
        title=room_config.title,
        user_id=user_id,
        project_id=room_config.project_id,
        initial_instruction=room_config.initial_instruction,
        config=room_config.model_dump(),
        created_at=datetime.now(),
    )
    with Session(get_engine()) as session:
        session.add(new_room)
        session.flush()
        session.commit()
        session.refresh(new_room)
        return new_room


def update_noob_room(room_id: str, updates: NoobRoomUpdate) -> NoobRoom:
    with Session(get_engine()) as session:
        db_room = session.get(NoobRoom, room_id)
        if not db_room:
            raise ValueError(f"NOOB room {room_id} not found")
        update_data = updates.model_dump(exclude_unset=True)
        db_room.sqlmodel_update(update_data)
        db_room.updated_at = datetime.now()
        session.add(db_room)
        session.commit()
        session.refresh(db_room)
        return db_room


def create_noob_thread(noob_room_id: str, thread: NoobThreadCreateRequest) -> NoobThread:
    new_thread = NoobThread(
        noob_room_id=noob_room_id,
        title=thread.title,
        keep_context=thread.keep_context,
        status="idle",
        created_at=datetime.now(),
    )
    with Session(get_engine()) as session:
        session.add(new_thread)
        session.flush()
        session.commit()
        session.refresh(new_thread)
        return new_thread


def list_noob_threads(noob_room_id: str) -> list[NoobThread]:
    with Session(get_engine()) as session:
        stmt = (
            select(NoobThread)
            .where(NoobThread.noob_room_id == noob_room_id)
            .order_by(NoobThread.created_at.asc())
        )
        return list(session.exec(stmt).all())


def get_noob_thread(thread_id: str) -> NoobThread | None:
    with Session(get_engine()) as session:
        return session.get(NoobThread, thread_id)


def get_active_noob_thread(noob_room_id: str) -> NoobThread | None:
    with Session(get_engine()) as session:
        stmt = (
            select(NoobThread)
            .where(NoobThread.noob_room_id == noob_room_id)
            .order_by(NoobThread.created_at.desc())
        )
        return session.exec(stmt).first()


def update_noob_thread_status(thread_id: str, status: str) -> NoobThread:
    with Session(get_engine()) as session:
        thread = session.get(NoobThread, thread_id)
        if not thread:
            raise ValueError(f"NOOB thread {thread_id} not found")
        thread.status = status
        thread.updated_at = datetime.now()
        session.add(thread)
        session.commit()
        session.refresh(thread)
        return thread

def list_rooms(user_id: str, project_id: str) -> list[TaskRoom]:
    with Session(get_engine()) as session:
        stmt = select(TaskRoom).where(TaskRoom.user_id == user_id, TaskRoom.project_id == project_id)
        return list(session.exec(stmt).all())
