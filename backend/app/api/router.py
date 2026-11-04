from fastapi import APIRouter

from app.api.routes import (
    auth,
    dashboard,
    detections,
    greenhouses,
    health,
    history,
    sensors,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(greenhouses.router)
api_router.include_router(dashboard.router)
api_router.include_router(sensors.router)
api_router.include_router(history.router)
api_router.include_router(detections.router)
