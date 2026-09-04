"""
climate_service.py - Historical Cyclone & Rainfall Climatology Analytics Engine
SIH 2026 Problem Statement SIH26068
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from config import settings
from models.schemas import CycloneRecordItem, ClimateTrendsResponse

def get_cyclone_and_climatology_trends() -> ClimateTrendsResponse:
    """Loads 131-year cyclone archive and January IMD climatology baselines."""
    file_path = settings.CYCLONE_CSV_PATH
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cyclone archive not found at {file_path}")
        
    df = pd.read_csv(file_path)
    
    # Clean column names
    col_map = {
        "Year": "year",
        "Cyclonic Disturbances - TOTAL": "disturbances",
        "Cyclones - TOTAL": "cyclones",
        "Severe Cyclones - TOTAL": "severe_cyclones",
        "Cyclones - BOB": "cyclones_bob",
        "Cyclones - AS": "cyclones_as"
    }
    df_clean = df.rename(columns=col_map)
    
    records: List[CycloneRecordItem] = []
    for _, row in df_clean.iterrows():
        records.append(CycloneRecordItem(
            year=int(row["year"]),
            cyclonic_disturbances_total=int(row["disturbances"]),
            cyclones_total=int(row["cyclones"]),
            severe_cyclones_total=int(row["severe_cyclones"]),
            cyclones_bob=int(row["cyclones_bob"]),
            cyclones_as=int(row["cyclones_as"])
        ))
        
    # Baseline climatological context from NetCDF analysis
    climatology_baseline = {
        "dataset_name": "IMD High-Resolution Gridded Rainfall Climatology (0.25° x 0.25°)",
        "source": "India Meteorological Department, National Climate Centre Pune",
        "january_all_india_land_mean_mm": 16.3,
        "january_peak_climatology_mm": 163.56,
        "sample_regional_baselines_mm": {
            "Nagpur (Vidarbha)": 13.5,
            "Lucknow (Northern Plains)": 14.8,
            "Kolkata (Lower Gangetic)": 14.0,
            "Chennai (Coromandel Coast)": 24.5,
            "Ahmedabad (Western Arid/Semi-arid)": 3.2
        },
        "cyclone_decadal_insights": {
            "most_active_cyclone_basin": "Bay of Bengal (77.8% of historical North Indian Ocean cyclones)",
            "arabian_sea_share": "20.1% of historical cyclones",
            "historical_observation_span": "1891–2021 (131 years continuous archive)"
        }
    }
    
    return ClimateTrendsResponse(
        description="Historical North Indian Ocean Cyclone Activity (1891-2021) & IMD Gridded Rainfall Climatology",
        data_source="IMD Cyclone E-Atlas & Gridded Climatology (data/raw/)",
        total_records=len(records),
        period="1891–2021",
        cyclone_trends=records,
        climatology_baseline=climatology_baseline
    )
