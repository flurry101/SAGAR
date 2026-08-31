from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.database import init_db
from app.api.health import router as health_router
from app.api.user import router as user_router
from app.api.trip import router as trip_router
from app.api.copilot import router as copilot_router
from app.api.assessment import router as assessment_router
from app.api.weather import router as weather_router
from app.api.marine import router as marine_router
from app.api.risk import router as risk_router


# Ensure tables are created
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(user_router, prefix="/api/v1/user", tags=["User"])
app.include_router(user_router, prefix="/user", tags=["User (Starter Compatibility)"])
app.include_router(trip_router, prefix="/api/v1", tags=["Trip Planning & LangGraph"])
app.include_router(copilot_router, prefix="/api/v1", tags=["Copilot & RAG"])
app.include_router(assessment_router, prefix="/api/v1", tags=["Assessments"])
app.include_router(weather_router, prefix="/api/v1", tags=["Weather & Hazards"])
app.include_router(marine_router, prefix="/api/v1", tags=["Marine & PFZ"])
app.include_router(risk_router, prefix="/api/v1", tags=["Deterministic Risk Engine"])


@app.get("/")
def read_root():
    return {"status": "ok", "message": f"{settings.APP_NAME} is running"}