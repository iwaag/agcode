from sqlmodel import Sequence

from agcode_domain.schema import SessionInfo, SessionListInfo
from agcode_infra.db.models import Session


def session_model_to_scheme(model: Session)->SessionInfo:
    return SessionInfo(id=model.id, title=model.title, task_started_at=model.task_started_at, finished_at=model.finished_at, config=model.config)

def session_model_sequence_to_sceme(session_squence: Sequence[Session])->SessionListInfo:
    return SessionListInfo(sessions=[session_model_to_scheme(session) for session in session_squence])
