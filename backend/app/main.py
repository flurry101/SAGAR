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
    security_headers_middleware,
)
from app.api.health import router as health_router
from app.api.user import router as user_router
from app.api.trip import router as trip_router
from app.api.copilot import router as copilot_router
from app.api.assessment import router as assessment_router
from app.api.weather import router as weather_router
from app.api.marine import router as marine_router
from app.api.risk import router as risk_router
from app.api.vessel import router as vessel_router
from app.api.voice import router as voice_router
from app.api.google_oauth import router as google_oauth_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables gracefully on startup
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Database initialization deferred or offline: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ORCA — Marine EcOsystem Reasoning with Collaborative Agents API",
    lifespan=lifespan,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID tracing middleware
app.middleware("http")(add_request_id_middleware)

# Security headers middleware
app.middleware("http")(security_headers_middleware)

# Global exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# API Route Registration
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(trip_router, prefix="/api/v1", tags=["Trip Planning & LangGraph"])
app.include_router(copilot_router, prefix="/api/v1", tags=["Fisherman Copilot & RAG"])
app.include_router(assessment_router, prefix="/api/v1", tags=["Assessments"])
app.include_router(vessel_router, prefix="/api/v1", tags=["Vessels"])
app.include_router(weather_router, prefix="/api/v1", tags=["Weather & Hazards"])
app.include_router(marine_router, prefix="/api/v1", tags=["Marine & PFZ"])
app.include_router(risk_router, prefix="/api/v1", tags=["Deterministic Risk Engine"])
app.include_router(voice_router, prefix="/api/v1/voice", tags=["Resilient Voice Architecture"])
app.include_router(user_router, prefix="/api/v1/user", tags=["User"])
app.include_router(user_router, prefix="/user", tags=["User (Starter Compatibility)"])
app.include_router(google_oauth_router, prefix="/api/v1", tags=["Google OAuth"])


@app.get("/")
def read_root():
    return {"status": "ok", "message": f"{settings.APP_NAME} is running"}
