"""
main.py - FastAPI Application Entry Point for WeatherGPT
SIH 2026 Problem Statement SIH26068
“From Weather Data to Actionable Decisions.”
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend and project root are in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import settings
from models.schemas import HealthResponse
from ml.predict import get_model
from api.weather import router as weather_router
from api.prediction import router as prediction_router
from api.alerts import router as alerts_router
from api.climate import router as climate_router
from api.farmer import router as farmer_router
from api.chatbot import router as chatbot_router
from api.location import router as location_router
from api.auth import router as auth_router
from services import auth_service

try:
    get_model()
    _ML_READY = True
except Exception:
    _ML_READY = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ML_READY
    print("="*60)
    print("  Initializing WeatherGPT Backend Engine (SIH26068)...")
    print(f"  Project Root: {PROJECT_ROOT}")
    try:
        get_model()
        _ML_READY = True
        print("  [OK] ML Risk Champion Model loaded successfully into memory.")
    except Exception as e:
        print(f"  [WARN] ML Model initialization warning: {e}")
        _ML_READY = False
    try:
        auth_service.init_db()
        print("  [OK] User Authentication SQLite Database initialized.")
    except Exception as e:
        print(f"  [WARN] User Auth DB initialization warning: {e}")
    print("="*60)
    yield
    print("[INFO] WeatherGPT Backend shutting down gracefully.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan
)

# CORS Configuration for React Vite Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow Vite frontend at :5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(weather_router)
app.include_router(prediction_router)
app.include_router(alerts_router)
app.include_router(climate_router)
app.include_router(farmer_router)
app.include_router(chatbot_router)
app.include_router(location_router)
app.include_router(auth_router)

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint to verify backend service and model readiness."""
    return HealthResponse(
        status="healthy",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        ml_model_loaded=_ML_READY,
        live_weather_api=settings.OPEN_METEO_API_URL,
        provenance_mode="Authentic Datasets (data/raw/) + Physics Demonstration ML"
    )

@app.get("/api/cyclone/live-systems", tags=["Cyclone Intelligence"])
def get_cyclone_live_systems():
    """Low-pressure systems detected from the LIVE mean-sea-level pressure field.

    This previously returned two hardcoded dictionaries, including a fictional
    storm named 'DANA' with a frozen timestamp. It now scans the Bay of Bengal
    and Arabian Sea for real pressure minima and reports only what it finds -
    or explicitly reports that nothing was found.

    Model estimate, never an official warning.
    """
    from services.cyclone_detect import detect_active_systems
    return detect_active_systems()


@app.get("/api/cyclone/risk", tags=["Cyclone Intelligence"])
def get_cyclone_risk(
    location: str = "Nagpur",
    lat: Optional[float] = None,
    lon: Optional[float] = None,
):
    """Cyclone risk for ONE location, from detected systems plus local conditions."""
    from services.cyclone_detect import cyclone_risk_for_location
    from services.weather_service import resolve_location, get_current_weather
    from services.alert_service import is_coastal_location

    name, state, lat_val, lon_val, _clim = resolve_location(location, lat, lon)

    gust = pressure = None
    try:
        cur = get_current_weather(location, lat=lat_val, lon=lon_val)
        gust = cur.current.wind_gust
        pressure = cur.current.surface_pressure
    except Exception as e:
        print(f"[WARN] Local conditions unavailable for cyclone risk at {name}: {e}")

    try:
        coastal = is_coastal_location(name, state, lat_val, lon_val)
    except Exception:
        coastal = None

    result = cyclone_risk_for_location(
        name, lat_val, lon_val,
        is_coastal=coastal, local_gust_kmh=gust, local_pressure_hpa=pressure)
    result.update({"state": state, "latitude": lat_val, "longitude": lon_val,
                   "is_coastal": coastal})
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
