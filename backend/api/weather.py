"""
weather.py - Weather Data & Forecast Endpoints for WeatherGPT
SIH 2026 Problem Statement SIH26068
"""

from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from config import settings
from models.schemas import WeatherCurrentResponse, WeatherForecastResponse, LocationItem
from services.weather_service import get_current_weather, get_forecast

router = APIRouter(prefix="/api/weather", tags=["Weather"])

@router.get("/current", response_model=WeatherCurrentResponse)
def get_current(
    location: str = Query("Nagpur", description="City, district, or address"),
    lat: Optional[float] = Query(None, description="Exact latitude of village or pin"),
    lon: Optional[float] = Query(None, description="Exact longitude of village or pin")
):
    """Fetches real-time current weather metrics with graceful offline baseline fallback."""
    return get_current_weather(location, lat=lat, lon=lon)

@router.get("/forecast", response_model=WeatherForecastResponse)
def get_daily_forecast(
    location: str = Query("Nagpur", description="City, district, or address"),
    days: int = Query(7, ge=1, le=14, description="Forecast horizon in days"),
    lat: Optional[float] = Query(None, description="Exact latitude of village or pin"),
    lon: Optional[float] = Query(None, description="Exact longitude of village or pin")
):
    """Fetches multi-day forecast with AI Weather Impact Risk Level per day."""
    return get_forecast(location, days=days, lat=lat, lon=lon)

@router.get("/location", response_model=List[LocationItem])
@router.get("/locations", response_model=List[LocationItem])
def list_available_locations():
    """Lists pre-indexed Indian cities and districts with coordinates and rainfall climatology."""
    items = []
    for k, loc in settings.LOCATIONS.items():
        items.append(LocationItem(
            name=loc["name"],
            state=loc["state"],
            latitude=loc["lat"],
            longitude=loc["lon"],
            rainfall_climatology_mm=loc["climatology"]
        ))
    return items

@router.get("/history")
def get_weather_history(limit: int = Query(30, ge=1, le=365)):
    """Returns historical daily observations from the local master dataset."""
    import pandas as pd
    master_path = settings.PROCESSED_DATA_DIR / "master_weather_dataset.csv"
    if not master_path.exists():
        return {
            "error": "Master dataset not yet created",
            "total_available": 0,
            "returned_records": 0,
            "records": []
        }
    try:
        df = pd.read_csv(master_path)
        df = df.fillna(0)
        sample = df.tail(limit).to_dict(orient="records")
        return {
            "total_available": len(df),
            "returned_records": len(sample),
            "data_source": "Open-Meteo & NRSC VIC Ground Observations (data/processed/master_weather_dataset.csv)",
            "records": sample
        }
    except Exception as e:
        return {
            "error": f"Failed to load history: {e}",
            "total_available": 0,
            "returned_records": 0,
            "records": []
        }
