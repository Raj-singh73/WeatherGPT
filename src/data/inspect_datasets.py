"""
inspect_datasets.py - Comprehensive Inspection of Raw Datasets for WeatherGPT
SIH 2026 Problem Statement SIH26068

Inspects:
1. Open-Meteo Hourly Weather CSV
2. NRSC VIC Model Rainfall CSV
3. Cyclone Frequency (1891-2021) CSV
4. Rainfall Climatology NetCDF (rf_p25_jan_clm.nc)

Outputs:
data/processed/dataset_report.json
"""

import os
import json
import numpy as np
import pandas as pd
import scipy.io as sio

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
REPORT_PATH = os.path.join(PROCESSED_DIR, "dataset_report.json")

def format_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def inspect_open_meteo():
    file_path = os.path.join(RAW_DIR, "open-meteo-20.56N78.93E245m.csv")
    file_size = os.path.getsize(file_path)
    
    # Header metadata in rows 0-1
    meta_df = pd.read_csv(file_path, nrows=1)
    lat = float(meta_df['latitude'].iloc[0]) if 'latitude' in meta_df.columns else 20.56239
    lon = float(meta_df['longitude'].iloc[0]) if 'longitude' in meta_df.columns else 78.93146
    elevation = float(meta_df['elevation'].iloc[0]) if 'elevation' in meta_df.columns else 245.0
    timezone = str(meta_df['timezone'].iloc[0]) if 'timezone' in meta_df.columns else "Asia/Kolkata"
    
    # Read actual hourly table starting at line 3 (index 2 in 0-indexed skiprows)
    df = pd.read_csv(file_path, skiprows=3)
    
    # Detect dates
    min_date = str(df['time'].min())
    max_date = str(df['time'].max())
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    missing_values = {col: int(df[col].isna().sum()) for col in df.columns}
    duplicate_count = int(df.duplicated().sum())
    
    return {
        "filename": "open-meteo-20.56N78.93E245m.csv",
        "file_type": "CSV (Station Hourly Observation/Reanalysis)",
        "size": format_bytes(file_size),
        "size_bytes": file_size,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": df.columns.tolist(),
        "missing_values": missing_values,
        "duplicate_count": duplicate_count,
        "date_range": {
            "start": min_date,
            "end": max_date,
            "temporal_resolution": "hourly"
        },
        "geographical_information": {
            "latitude": lat,
            "longitude": lon,
            "elevation_m": elevation,
            "timezone": timezone,
            "approximate_region": "Central India (near Wardha / Nagpur, Maharashtra)"
        },
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "sample_statistics": {
            col: {
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": round(float(df[col].mean()), 2)
            } for col in numeric_cols
        },
        "recommended_usage": "Core historical meteorological baseline. Convert hourly data into daily statistics (temperature min/mean/max, precipitation total, wind gusts, pressure) for feature engineering and ML training."
    }

def inspect_nrsc_rainfall():
    file_path = os.path.join(RAW_DIR, "nrsc_vic_rainfall.csv")
    file_size = os.path.getsize(file_path)
    
    df = pd.read_csv(file_path)
    
    min_date = str(df['Date'].min()) if 'Date' in df.columns else "N/A"
    max_date = str(df['Date'].max()) if 'Date' in df.columns else "N/A"
    
    states = df['State'].dropna().unique().tolist() if 'State' in df.columns else []
    districts = df['District'].dropna().unique().tolist() if 'District' in df.columns else []
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    missing_values = {col: int(df[col].isna().sum()) for col in df.columns}
    duplicate_count = int(df.duplicated().sum())
    
    return {
        "filename": "nrsc_vic_rainfall.csv",
        "file_type": "CSV (Hydrological Model Daily Output)",
        "size": format_bytes(file_size),
        "size_bytes": file_size,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": df.columns.tolist(),
        "missing_values": missing_values,
        "duplicate_count": duplicate_count,
        "date_range": {
            "start": min_date,
            "end": max_date,
            "temporal_resolution": "daily"
        },
        "geographical_information": {
            "states": states,
            "district_count": len(districts),
            "sample_districts": districts[:10]
        },
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "sample_statistics": {
            "avg_rainfall_mm": {
                "min": float(df['Avg_rainfall'].min()) if 'Avg_rainfall' in df.columns else 0.0,
                "max": float(df['Avg_rainfall'].max()) if 'Avg_rainfall' in df.columns else 0.0,
                "mean": round(float(df['Avg_rainfall'].mean()), 4) if 'Avg_rainfall' in df.columns else 0.0
            }
        },
        "recommended_usage": "Indian district-level daily rainfall validation and multi-day accumulation (1d, 3d, 7d, 30d rolling rainfall) for agricultural and soil moisture context."
    }

def inspect_cyclone_frequency():
    file_path = os.path.join(RAW_DIR, "annualFrequency-1891-2021.csv")
    file_size = os.path.getsize(file_path)
    
    df = pd.read_csv(file_path)
    
    min_year = int(df['Year'].min()) if 'Year' in df.columns else 1891
    max_year = int(df['Year'].max()) if 'Year' in df.columns else 2021
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    missing_values = {col: int(df[col].isna().sum()) for col in df.columns}
    duplicate_count = int(df.duplicated().sum())
    
    return {
        "filename": "annualFrequency-1891-2021.csv",
        "file_type": "CSV (Historical Climate & Disaster Archive)",
        "size": format_bytes(file_size),
        "size_bytes": file_size,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": df.columns.tolist(),
        "missing_values": missing_values,
        "duplicate_count": duplicate_count,
        "date_range": {
            "start_year": min_year,
            "end_year": max_year,
            "total_years": max_year - min_year + 1,
            "temporal_resolution": "annual"
        },
        "geographical_information": {
            "ocean_basins": ["Bay of Bengal (BOB)", "Arabian Sea (AS)", "Land"],
            "region": "North Indian Ocean (India coastal & mainland)"
        },
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "summary_totals": {
            "total_cyclones_recorded": int(df['Cyclones - TOTAL'].sum()) if 'Cyclones - TOTAL' in df.columns else 0,
            "total_severe_cyclones": int(df['Severe Cyclones - TOTAL'].sum()) if 'Severe Cyclones - TOTAL' in df.columns else 0,
            "cyclones_bob": int(df['Cyclones - BOB'].sum()) if 'Cyclones - BOB' in df.columns else 0,
            "cyclones_as": int(df['Cyclones - AS'].sum()) if 'Cyclones - AS' in df.columns else 0
        },
        "recommended_usage": "Macro-climate analytics and disaster frequency trends (131 years). Used on Climate Analytics dashboard to visualize long-term cyclone frequency in Bay of Bengal vs Arabian Sea. NOT used for short-term daily weather ML."
    }

def inspect_netcdf_climatology():
    file_path = os.path.join(RAW_DIR, "rf_p25_jan_clm.nc")
    file_size = os.path.getsize(file_path)
    
    f = sio.netcdf_file(file_path, 'r', mmap=False)
    
    variables = list(f.variables.keys())
    lats = f.variables['lat'].data.copy()
    lons = f.variables['lon'].data.copy()
    rf_data = f.variables['rf'].data.copy()
    f.close()
    
    # Calculate statistics on valid data
    valid_rf = rf_data[~np.isnan(rf_data)]
    valid_rf = valid_rf[valid_rf >= 0]
    
    return {
        "filename": "rf_p25_jan_clm.nc",
        "file_type": "NetCDF-3 64-bit Offset (Gridded Climatology)",
        "size": format_bytes(file_size),
        "size_bytes": file_size,
        "dimensions": {
            "latitude_points": int(len(lats)),
            "longitude_points": int(len(lons)),
            "grid_resolution_degrees": 0.25
        },
        "variables": variables,
        "geographical_information": {
            "latitude_range": [float(lats.min()), float(lats.max())],
            "longitude_range": [float(lons.min()), float(lons.max())],
            "coverage": "Indian Subcontinent (0.25 x 0.25 deg IMD high-resolution grid)"
        },
        "climatology_period": "January Climatology (rf_p25_jan_clm)",
        "grid_statistics_mm": {
            "min": float(np.min(valid_rf)) if len(valid_rf) > 0 else 0.0,
            "max": round(float(np.max(valid_rf)), 2) if len(valid_rf) > 0 else 0.0,
            "mean": round(float(np.mean(valid_rf)), 2) if len(valid_rf) > 0 else 0.0
        },
        "recommended_usage": "Extract spatial baseline climatological rainfall for any coordinate (lat, lon) using 2D nearest neighbor or bilinear interpolation. Used to compute rainfall anomaly: (actual_rainfall - climatology) / max(climatology, epsilon)."
    }

def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    report = {
        "project": "WeatherGPT - SIH 2026 Problem Statement SIH26068",
        "title": "Comprehensive Dataset Inspection and Provenance Report",
        "timestamp": pd.Timestamp.now().isoformat(),
        "datasets": {
            "dataset_1_open_meteo": inspect_open_meteo(),
            "dataset_2_nrsc_vic_rainfall": inspect_nrsc_rainfall(),
            "dataset_3_cyclone_frequency": inspect_cyclone_frequency(),
            "dataset_4_rainfall_climatology_netcdf": inspect_netcdf_climatology()
        },
        "summary": {
            "total_real_datasets": 4,
            "provenance_policy": "Strict separation between REAL DATA (data/raw/) and SYNTHETIC DEMONSTRATION LABELS (data/synthetic/)."
        }
    }
    
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    print(f"[OK] Dataset inspection complete. Report saved to: {REPORT_PATH}")

if __name__ == "__main__":
    main()
