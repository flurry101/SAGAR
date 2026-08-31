# attr: m1
# [api routers package init]
from app.api.health import router as health_router
from app.api.user import router as user_router
from app.api.chat import router as chat_router
from app.api.copilot import router as copilot_router
from app.api.assessment import router as assessment_router
from app.api.trip import router as trip_router
from app.api.vessel import router as vessel_router

__all__ = [
    "health_router",
    "user_router",
    "chat_router",
    "copilot_router",
    "assessment_router",
    "trip_router",
    "vessel_router",
]
# attr: m1
