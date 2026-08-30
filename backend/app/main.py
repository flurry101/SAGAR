from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.database import init_db
from app.api.health import router as health_router
from app.api.user import router as user_router


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


@app.get("/")
def read_root():
    return {"status": "ok", "message": f"{settings.APP_NAME} is running"}