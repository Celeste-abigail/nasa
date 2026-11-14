from fastapi import APIRouter

from app.api.v1 import astronauts, measurements, monitoring
from app.modules.cortisol import router as cortisol_router

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(astronauts.router)
api_router.include_router(measurements.router)
api_router.include_router(cortisol_router.router)
