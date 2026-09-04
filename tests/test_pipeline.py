"""
test_pipeline.py - Pytest Suite for Data Processing, Climatology & ML Inference
SIH 2026 Problem Statement SIH26068
"""

import os
import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "data"))

from clean_data import clean_open_meteo, clean_nrsc_rainfall, clean_netcdf_climatology
from feature_engineering import lookup_climatology, get_season
from ml.predict import predict_weather_risk

def test_data_cleaning():
    df_om, meta = clean_open_meteo()
    assert len(df_om) > 40000
    assert "temperature_2m" in df_om.columns
    assert df_om["rain_mm"].min() >= 0.0

    df_nrsc = clean_nrsc_rainfall()
    assert len(df_nrsc) > 25000
    assert df_nrsc["avg_rainfall_mm"].min() >= 0.0

def test_netcdf_climatology():
    lats, lons, rf = clean_netcdf_climatology()
    assert lats.shape[0] == 129
    assert lons.shape[0] == 135
    assert rf.shape == (129, 135)
    
    # Test Nagpur lookup (21.14°N, 79.08°E)
    val = lookup_climatology(21.14, 79.08, lats, lons, rf)
    assert val > 0.0

def test_seasonal_calendar():
    assert get_season(1) == "Winter"
    assert get_season(4) == "Summer"
    assert get_season(7) == "Monsoon"
    assert get_season(10) == "Post-Monsoon"

def test_ml_prediction_bounds():
    sample = {
        "location": "Nagpur",
        "temperature_mean": 28.0,
        "temperature_max": 33.0,
        "temperature_min": 24.0,
        "humidity_mean": 75.0,
        "humidity_max": 90.0,
        "wind_speed": 18.0,
        "wind_gust": 35.0,
        "surface_pressure": 1005.0,
        "precipitation": 12.0,
        "rainfall_1d": 12.0,
        "rainfall_3d": 25.0,
        "rainfall_7d": 45.0,
        "rainfall_30d": 110.0,
        "rainfall_climatology": 13.5,
        "rainfall_anomaly": -0.11,
        "rainfall_anomaly_percent": -11.0,
        "temperature_change_24h": 0.2,
        "rainfall_change_24h": 2.0,
        "soil_moisture": 45.0,
        "month": 7,
        "day_of_year": 195,
        "season": "Monsoon"
    }
    pred = predict_weather_risk(sample)
    assert 0.0 <= pred["risk_score"] <= 100.0
    assert pred["risk_level"] in ["LOW", "MODERATE", "HIGH", "SEVERE"]
    assert len(pred["key_factors"]) > 0
    assert "disclaimer" in pred
