import logging
from fastapi import Depends, FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from routers.session import router as session_router

app = FastAPI(
    title="agcode"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(session_router, prefix="/session", tags=["session"])

logging.basicConfig(level=logging.DEBUG, force=True)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logging.error(f"caught exception: {exc.detail}", exc_info=True)
    return exc
    
@app.get("/health")
async def health():
    return {"status": "ok"}