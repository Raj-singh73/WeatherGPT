"""
merge_datasets.py - Assembles Master Weather Feature Dataset
SIH 2026 Problem Statement SIH26068
"""

import os
import pandas as pd
from feature_engineering import engineer_open_meteo_daily, engineer_nrsc_daily

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
MASTER_OUTPUT_PATH = os.path.join(PROCESSED_DIR, "master_weather_dataset.csv")

# Standardized Master Column Order
MASTER_COLUMNS = [
    "date",
    "state",
    "district",
    "latitude",
    "longitude",
    "month",
    "day_of_year",
    "season",
    "temperature_mean",
    "temperature_max",
    "temperature_min",
    "humidity_mean",
    "humidity_max",
    "wind_speed",
    "wind_gust",
    "surface_pressure",
    "precipitation",
    "rainfall_1d",
    "rainfall_3d",
    "rainfall_7d",
    "rainfall_30d",
    "rainfall_climatology",
    "rainfall_anomaly",
    "rainfall_anomaly_percent",
    "temperature_change_24h",
    "rainfall_change_24h",
    "soil_moisture",
    "data_source",
    "is_real"
]

def build_master_dataset() -> pd.DataFrame:
    """Combines real Open-Meteo station series and NRSC VIC district series without false cross-joins."""
    print("[INFO] Engineering Open-Meteo daily station features...")
    df_om = engineer_open_meteo_daily()
    
    print("[INFO] Engineering NRSC VIC district daily rainfall features...")
    df_nrsc = engineer_nrsc_daily()
    
    # Select standardized columns
    df_om_aligned = df_om[MASTER_COLUMNS].copy()
    df_nrsc_aligned = df_nrsc[MASTER_COLUMNS].copy()
    
    # Combine datasets
    master_df = pd.concat([df_om_aligned, df_nrsc_aligned], ignore_index=True)
    master_df['date'] = pd.to_datetime(master_df['date'])
    master_df = master_df.sort_values(['state', 'district', 'date']).reset_index(drop=True)
    
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    master_df.to_csv(MASTER_OUTPUT_PATH, index=False)
    
    print(f"[OK] Master weather dataset assembled successfully:")
    print(f" -> File: {MASTER_OUTPUT_PATH}")
    print(f" -> Total rows: {len(master_df)}")
    print(f" -> Total columns: {len(master_df.columns)}")
    print(f" -> Open-Meteo station records: {len(df_om)}")
    print(f" -> NRSC VIC district records: {len(df_nrsc)}")
    print(f" -> All rows verified as real data: {master_df['is_real'].all()}")
    
    return master_df

if __name__ == "__main__":
    build_master_dataset()
