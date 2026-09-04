"""
clean_data.py - Data Cleaning & Standardization Module for WeatherGPT
SIH 2026 Problem Statement SIH26068
"""

import os
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
from load_data import load_open_meteo_raw, load_nrsc_rainfall_raw, load_cyclone_frequency_raw, load_netcdf_climatology_raw

def clean_open_meteo() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Cleans Open-Meteo hourly data: standardizes column names, types, and removes artifacts."""
    df, metadata = load_open_meteo_raw()
    
    # Rename columns to standardized names
    rename_dict = {
        "time": "timestamp",
        "temperature_2m (°C)": "temperature_2m",
        "relative_humidity_2m (%)": "relative_humidity_2m",
        "rain (mm)": "rain_mm",
        "wind_direction_10m (°)": "wind_direction_10m",
        "wind_gusts_10m (km/h)": "wind_gusts_10m",
        "surface_pressure (hPa)": "surface_pressure",
        "precipitation (mm)": "precipitation_mm"
    }
    df = df.rename(columns=rename_dict)
    
    # Convert timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Ensure physical limits
    df['rain_mm'] = df['rain_mm'].clip(lower=0.0)
    df['precipitation_mm'] = df['precipitation_mm'].clip(lower=0.0)
    df['relative_humidity_2m'] = df['relative_humidity_2m'].clip(lower=0.0, upper=100.0)
    df['wind_gusts_10m'] = df['wind_gusts_10m'].clip(lower=0.0)
    
    # Check nulls
    if df.isna().sum().sum() > 0:
        df = df.interpolate(method='linear').bfill().ffill()
        
    return df, metadata

def clean_nrsc_rainfall() -> pd.DataFrame:
    """Cleans ISRO NRSC VIC daily rainfall data: standardizes district names and clips negative artifacts."""
    df = load_nrsc_rainfall_raw()
    
    rename_dict = {
        "State": "state",
        "District": "district",
        "Date": "date",
        "Year": "year",
        "Month": "month",
        "Avg_rainfall": "avg_rainfall_mm",
        "Agency_name": "agency_name"
    }
    df = df.rename(columns=rename_dict)
    
    # Format dates
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['year'].astype(int)
    df['month'] = df['month'].astype(int)
    
    # Clean numerical model floating artifacts (< 0 to 0.0)
    df['avg_rainfall_mm'] = df['avg_rainfall_mm'].clip(lower=0.0)
    
    # Clean string columns
    df['state'] = df['state'].astype(str).str.strip()
    df['district'] = df['district'].astype(str).str.strip()
    
    df = df.sort_values(['district', 'date']).reset_index(drop=True)
    return df

def clean_cyclone_frequency() -> pd.DataFrame:
    """Cleans historical cyclone frequency archive (1891-2021)."""
    df = load_cyclone_frequency_raw()
    
    rename_dict = {
        "Year": "year",
        "Cyclonic Disturbances - BOB": "cyclonic_disturbances_bob",
        "Cyclonic Disturbances - AS": "cyclonic_disturbances_as",
        "Cyclonic Disturbances - LAND": "cyclonic_disturbances_land",
        "Cyclonic Disturbances - TOTAL": "cyclonic_disturbances_total",
        "Cyclones - BOB": "cyclones_bob",
        "Cyclones - AS": "cyclones_as",
        "Cyclones - LAND": "cyclones_land",
        "Cyclones - TOTAL": "cyclones_total",
        "Severe Cyclones - BOB": "severe_cyclones_bob",
        "Severe Cyclones - AS": "severe_cyclones_as",
        "Severe Cyclones - LAND": "severe_cyclones_land",
        "Severe Cyclones - TOTAL": "severe_cyclones_total"
    }
    df = df.rename(columns=rename_dict)
    df['year'] = df['year'].astype(int)
    
    for col in df.columns:
        if col != 'year':
            df[col] = df[col].clip(lower=0).astype(int)
            
    df = df.sort_values('year').reset_index(drop=True)
    return df

def clean_netcdf_climatology() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Cleans NetCDF rainfall climatology matrix, replacing fill values and NaNs with valid boundary values."""
    lats, lons, rf = load_netcdf_climatology_raw()
    
    # Create a clean copy where NaNs and negative fill-values are set to 0.0
    rf_clean = np.where(np.isnan(rf) | (rf < 0), 0.0, rf)
    return lats, lons, rf_clean

if __name__ == "__main__":
    df_om, meta = clean_open_meteo()
    print(f"[OK] Cleaned Open-Meteo: {df_om.shape}, columns: {list(df_om.columns)}")
    df_nrsc = clean_nrsc_rainfall()
    print(f"[OK] Cleaned NRSC VIC: {df_nrsc.shape}, min rainfall: {df_nrsc['avg_rainfall_mm'].min()}")
    df_cyc = clean_cyclone_frequency()
    print(f"[OK] Cleaned Cyclones: {df_cyc.shape}, years: {df_cyc['year'].min()}-{df_cyc['year'].max()}")
    lats, lons, rf = clean_netcdf_climatology()
    print(f"[OK] Cleaned NetCDF grid: min={rf.min()}, max={rf.max():.2f}")
