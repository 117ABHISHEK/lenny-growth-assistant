import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import sessions, chat, health

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("lenny_assistant")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lenny Growth Assistant backend starting up")
    from app.database import init_models
    await init_models()
    yield
    logger.info("Shutting down")

app = FastAPI(title="Lenny Growth Assistant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error", "detail": str(exc)})

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(chat.router)