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

def assess_risk_from_daily_features(
    location: str,
    lat: float,
    lon: float,
    t_max: float,
    t_min: float,
    precipitation: float,
    wind_gust: float,
    climatology: float = 12.0,
    humidity: float = 65.0
) -> Dict[str, Any]:
    """Helper to predict risk from basic forecast parameters."""
    t_mean = (t_max + t_min) / 2.0
    anomaly = (precipitation - climatology) / max(climatology, 0.01)
    
    # Soil moisture proxy: higher if rain > 20mm
    soil_moisture = 45.0 + min(precipitation * 0.8, 45.0)
    
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
        "month": 7,
        "day_of_year": 195,
        "season": "Monsoon" if precipitation > 5.0 else "Summer"
    }
    
    return predict_weather_risk(weather_input)

def predict_custom_risk(req_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Direct inference entry point for POST /api/predict/risk."""
    return predict_weather_risk(req_dict)
