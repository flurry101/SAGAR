# attr: m1
# [fastapi main application entrypoint]
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.database import init_db
from app.core.middleware import (
    add_request_id_middleware,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.api.health import router as health_router
from app.api.user import router as user_router
from app.api.chat import router as chat_router
from app.api.copilot import router as copilot_router
from app.api.assessment import router as assessment_router
from app.api.trip import router as trip_router
from app.api.vessel import router as vessel_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # [initialize database tables gracefully on startup]
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Database initialization deferred or offline: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    description="ORCA — Marine EcOsystem Reasoning with Collaborative Agents API",
)

# [cors configuration]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# [request id tracing middleware]
app.middleware("http")(add_request_id_middleware)

# [global exception handlers]
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# [api route registration]
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(chat_router, prefix="/api/v1", tags=["Trip Planner (LangGraph)"])
app.include_router(copilot_router, prefix="/api/v1", tags=["Fisherman Copilot (Chatbot)"])
app.include_router(assessment_router, prefix="/api/v1", tags=["Assessments"])
app.include_router(trip_router, prefix="/api/v1", tags=["Trip Planning"])
app.include_router(vessel_router, prefix="/api/v1", tags=["Vessels"])
app.include_router(user_router, prefix="/api/v1/user", tags=["User"])
app.include_router(user_router, prefix="/user", tags=["User (Starter Compatibility)"])


@app.get("/")
def read_root():
    # [service health root check]
    return {"status": "ok", "message": f"{settings.APP_NAME} is running"}
# attr: m1