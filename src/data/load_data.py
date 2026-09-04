"""
load_data.py - Data Loading & Ingestion Module for WeatherGPT
SIH 2026 Problem Statement SIH26068
"""

import os
import pandas as pd
import numpy as np
import scipy.io as sio
from typing import Dict, Any, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

def load_open_meteo_raw() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Loads Open-Meteo hourly CSV, extracting station metadata and timeseries."""
    file_path = os.path.join(RAW_DIR, "open-meteo-20.56N78.93E245m.csv")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Open-Meteo dataset not found at {file_path}")
    
    # Extract metadata row 0
    meta_df = pd.read_csv(file_path, nrows=1)
    metadata = {
        "latitude": float(meta_df['latitude'].iloc[0]) if 'latitude' in meta_df.columns else 20.56239,
        "longitude": float(meta_df['longitude'].iloc[0]) if 'longitude' in meta_df.columns else 78.93146,
        "elevation": float(meta_df['elevation'].iloc[0]) if 'elevation' in meta_df.columns else 245.0,
        "timezone": str(meta_df['timezone'].iloc[0]) if 'timezone' in meta_df.columns else "Asia/Kolkata"
    }
    
    # Load hourly observation records starting row 3
    df = pd.read_csv(file_path, skiprows=3)
    return df, metadata

def load_nrsc_rainfall_raw() -> pd.DataFrame:
    """Loads ISRO NRSC VIC daily rainfall dataset."""
    file_path = os.path.join(RAW_DIR, "nrsc_vic_rainfall.csv")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"NRSC VIC rainfall dataset not found at {file_path}")
    
    df = pd.read_csv(file_path)
    return df

def load_cyclone_frequency_raw() -> pd.DataFrame:
    """Loads historical cyclone frequency archive (1891-2021)."""
    file_path = os.path.join(RAW_DIR, "annualFrequency-1891-2021.csv")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cyclone frequency dataset not found at {file_path}")
    
    df = pd.read_csv(file_path)
    return df

def load_netcdf_climatology_raw() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Loads gridded rainfall climatology NetCDF file."""
    file_path = os.path.join(RAW_DIR, "rf_p25_jan_clm.nc")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Rainfall climatology NetCDF not found at {file_path}")
    
    f = sio.netcdf_file(file_path, 'r', mmap=False)
    lats = f.variables['lat'].data.copy()
    lons = f.variables['lon'].data.copy()
    rf = f.variables['rf'].data.copy()
    f.close()
    
    return lats, lons, rf

if __name__ == "__main__":
    df_om, meta = load_open_meteo_raw()
    print(f"[OK] Open-Meteo loaded: {len(df_om)} rows. Metadata: {meta}")
    df_nrsc = load_nrsc_rainfall_raw()
    print(f"[OK] NRSC VIC loaded: {len(df_nrsc)} rows.")
    df_cyc = load_cyclone_frequency_raw()
    print(f"[OK] Cyclone archive loaded: {len(df_cyc)} rows.")
    lats, lons, rf = load_netcdf_climatology_raw()
    print(f"[OK] NetCDF Climatology loaded: lats {lats.shape}, lons {lons.shape}, grid {rf.shape}.")
