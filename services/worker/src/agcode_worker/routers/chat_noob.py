import os

from fastapi import APIRouter

router = APIRouter()
AGENT_PROVIDER = os.getenv("AGENT_PROVIDER")
if AGENT_PROVIDER != "LOCAL":
    raise Exception("AGENT_PROVIDER must be LOCAL in noob worker")
LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL")
if LOCAL_LLM_URL is None:
    raise Exception("LOCAL_LLM_URL must be set in noob worker")

@router.post("/realtime", summary="open real time chat via Websocket")
async def realtime_chat():
    pass