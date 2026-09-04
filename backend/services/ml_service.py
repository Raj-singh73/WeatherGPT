"""
ml_service.py - ML Risk Assessment Service Wrapper for WeatherGPT
SIH 2026 Problem Statement SIH26068
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure ml package is importable
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.predict import predict_weather_risk

from datetime import datetime
from typing import Dict, Any, Optional

def get_meteorological_season(month: int) -> str:
    """Returns official IMD meteorological season label matching model training."""
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Summer"
    elif month in [6, 7, 8, 9]:
        return "Monsoon"
    else:
        return "Post-Monsoon"

def assess_risk_from_daily_features(
    location: str,
    lat: float,
    lon: float,
    t_max: float,
    t_min: float,
    precipitation: float,
    wind_gust: float,
    climatology: float = 12.0,
    humidity: float = 65.0,
    date_str: Optional[str] = None
) -> Dict[str, Any]:
    """Helper to predict risk from basic forecast parameters with dynamic date/season grounding."""
    t_mean = (t_max + t_min) / 2.0
    anomaly = (precipitation - climatology) / max(climatology, 0.01)
    
    # Soil moisture proxy: scales with rain volume
    soil_moisture = float(np_clip_soil(precipitation))
    
    # Determine realistic month, day_of_year, and season
    if date_str:
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
            month = dt.month
            doy = dt.timetuple().tm_yday
        except Exception:
            now = datetime.now()
            month = now.month
            doy = now.timetuple().tm_yday
    else:
        now = datetime.now()
        month = now.month
        doy = now.timetuple().tm_yday

    season = get_meteorological_season(month)
    
    weather_input = {
        "location": location,
        "latitude": lat,
        "longitude": lon,
        "temperature_mean": t_mean,
        "temperature_max": t_max,
        "temperature_min": t_min,
        "humidity_mean": humidity,
        "humidity_max": min(humidity + 15.0, 98.0),
        "wind_speed": wind_gust * 0.65,
        "wind_gust": wind_gust,
        "surface_pressure": 1005.0 if precipitation < 20 else 995.0,
        "precipitation": precipitation,
        "rainfall_1d": precipitation,
        "rainfall_3d": precipitation * 1.5,
        "rainfall_7d": precipitation * 2.2,
        "rainfall_30d": precipitation * 3.5,
        "rainfall_climatology": climatology,
        "rainfall_anomaly": anomaly,
        "rainfall_anomaly_percent": anomaly * 100.0,
        "temperature_change_24h": 0.0,
        "rainfall_change_24h": precipitation,
        "soil_moisture": soil_moisture,
        "month": month,
        "day_of_year": doy,
        "season": season
    }
    
    return predict_weather_risk(weather_input)

def np_clip_soil(precipitation: float) -> float:
    return min(95.0, 42.0 + min(precipitation * 0.75, 48.0))

def predict_custom_risk(req_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Direct inference entry point for POST /api/predict/risk.
    Intelligently synchronizes physical features to avoid distorted predictions from partial payloads.
    """
    d = dict(req_dict)

    # 1. Temperature synchronization
    t_max = d.get("temperature_max")
    t_min = d.get("temperature_min")
    if t_max is not None and t_min is not None:
        if d.get("temperature_mean") is None:
            d["temperature_mean"] = (t_max + t_min) / 2.0
    elif d.get("temperature_mean") is None:
        d["temperature_mean"] = 28.0

    if d.get("temperature_max") is None:
        d["temperature_max"] = d["temperature_mean"] + 3.5
    if d.get("temperature_min") is None:
        d["temperature_min"] = d["temperature_mean"] - 4.5

    # 2. Rainfall synchronization
    precip = float(d.get("precipitation") if d.get("precipitation") is not None else 0.0)
    d["precipitation"] = precip

    if d.get("rainfall_1d") is None:
        d["rainfall_1d"] = precip

    r1d = float(d["rainfall_1d"])
    if d.get("rainfall_3d") is None:
        d["rainfall_3d"] = round(r1d * 1.5, 1)
    if d.get("rainfall_7d") is None:
        d["rainfall_7d"] = round(r1d * 2.2, 1)
    if d.get("rainfall_30d") is None:
        d["rainfall_30d"] = round(r1d * 3.5, 1)

    # 3. Climatology & anomaly
    clim = float(d.get("rainfall_climatology") or 12.0)
    d["rainfall_climatology"] = clim
    anomaly = (r1d - clim) / max(clim, 0.01)
    if d.get("rainfall_anomaly") is None:
        d["rainfall_anomaly"] = round(anomaly, 3)
    if d.get("rainfall_anomaly_percent") is None:
        d["rainfall_anomaly_percent"] = round(anomaly * 100.0, 1)

    # 4. Wind synchronization
    if d.get("wind_speed") is None:
        d["wind_speed"] = 15.0
    if d.get("wind_gust") is None:
        d["wind_gust"] = round(float(d["wind_speed"]) * 1.5, 1)

    # 5. Soil moisture dynamic derivation
    if d.get("soil_moisture") is None:
        d["soil_moisture"] = round(np_clip_soil(r1d), 1)

    # 6. Pressure default
    if d.get("surface_pressure") is None:
        d["surface_pressure"] = 1005.0 if r1d < 25.0 else 995.0

    # 7. Humidity defaults
    if d.get("humidity_mean") is None:
        d["humidity_mean"] = 70.0 if r1d < 10.0 else 85.0
    if d.get("humidity_max") is None:
        d["humidity_max"] = min(float(d["humidity_mean"]) + 12.0, 98.0)

    # 8. Date and season
    now = datetime.now()
    if d.get("month") is None:
        d["month"] = now.month
    if d.get("day_of_year") is None:
        d["day_of_year"] = now.timetuple().tm_yday
    if not d.get("season"):
        d["season"] = get_meteorological_season(d["month"])

    return predict_weather_risk(d)
