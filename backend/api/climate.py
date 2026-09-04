"""
climate.py - Climate Analytics API Router for WeatherGPT
SIH 2026 Problem Statement SIH26068
"""

from fastapi import APIRouter
from models.schemas import ClimateTrendsResponse
from services.climate_service import get_cyclone_and_climatology_trends

router = APIRouter(prefix="/api/climate", tags=["Climate Analytics"])

@router.get("/trends", response_model=ClimateTrendsResponse)
def get_climate_analytics():
    """Retrieves 131-year North Indian Ocean cyclone trends and IMD baseline rainfall climatology."""
    return get_cyclone_and_climatology_trends()
