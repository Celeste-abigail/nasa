from fastapi import APIRouter

from app.api.v1 import astronauts, measurements, monitoring

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(astronauts.router)
api_router.include_router(measurements.router)
