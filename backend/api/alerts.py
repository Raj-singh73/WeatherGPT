"""
alerts.py - Multi-hazard Alerts API Router for WeatherGPT
SIH 2026 Problem Statement SIH26068
"""

from fastapi import APIRouter, Query
from typing import Optional
from models.schemas import AlertsResponse
from services.alert_service import generate_alerts

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

@router.get("", response_model=AlertsResponse)
def get_alerts(
    location: str = Query("Nagpur", description="Location name"),
    lat: Optional[float] = Query(None, description="Exact latitude of village or pin"),
    lon: Optional[float] = Query(None, description="Exact longitude of village or pin")
):
    """Retrieves active multi-hazard alerts with transparent AI DEMO ALERT provenance."""
    return generate_alerts(location, lat=lat, lon=lon)
