class RoomError(Exception):
    pass


class RoomNotFoundError(RoomError):
    pass


class RoomAccessDeniedError(RoomError):
    pass


class NoobRoomConflictError(RoomError):
    pass


class NoobThreadNotFoundError(RoomError):
    pass


class MissionNotFoundError(RoomError):
    pass


class MissionAccessDeniedError(RoomError):
    pass


class MissionConflictError(RoomError):
    pass
