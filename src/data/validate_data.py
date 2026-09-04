"""
validate_data.py - Data Quality & Physical Consistency Validation
SIH 2026 Problem Statement SIH26068
"""

import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MASTER_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "master_weather_dataset.csv")

def validate_master_dataset(file_path: str = MASTER_DATA_PATH) -> bool:
    """Performs rigorous data quality and meteorological consistency validation."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Master dataset not found at {file_path}")
    
    df = pd.read_csv(file_path)
    print(f"[VALIDATION] Validating dataset: {file_path} ({len(df)} rows)")
    
    errors = []
    warnings = []
    
    # 1. Missing Values
    null_counts = df.isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]
    if len(cols_with_nulls) > 0:
        errors.append(f"Missing values found in columns: {dict(cols_with_nulls)}")
    else:
        print("  [OK] Zero missing values across all columns.")
        
    # 2. Duplicate Rows
    dupes = df.duplicated(subset=['state', 'district', 'date']).sum()
    if dupes > 0:
        errors.append(f"Found {dupes} duplicate (state, district, date) records.")
    else:
        print("  [OK] Zero duplicate records.")
        
    # 3. Physical Meteorological Range Checks
    # Temperature min <= mean <= max
    temp_inversion = (df['temperature_min'] > df['temperature_mean']) | (df['temperature_mean'] > df['temperature_max'])
    if temp_inversion.sum() > 0:
        errors.append(f"Found {temp_inversion.sum()} temperature inversion violations (min > mean or mean > max).")
    else:
        print("  [OK] Temperature physical bounds verified (min <= mean <= max).")
        
    # Relative humidity between 0 and 100
    rh_violation = (df['humidity_mean'] < 0) | (df['humidity_mean'] > 100) | (df['humidity_max'] < 0) | (df['humidity_max'] > 100)
    if rh_violation.sum() > 0:
        errors.append(f"Found {rh_violation.sum()} humidity range violations.")
    else:
        print("  [OK] Humidity physical range verified (0% <= RH <= 100%).")
        
    # Rainfall non-negative
    rain_neg = (df['rainfall_1d'] < 0) | (df['rainfall_3d'] < 0) | (df['rainfall_7d'] < 0)
    if rain_neg.sum() > 0:
        errors.append(f"Found {rain_neg.sum()} negative rainfall values.")
    else:
        print("  [OK] Rainfall non-negativity verified (rainfall >= 0 mm).")
        
    # Multi-day rainfall monotonic consistency (3d >= 1d)
    rain_consistency = df['rainfall_3d'] + 0.001 < df['rainfall_1d']
    if rain_consistency.sum() > 0:
        errors.append(f"Found {rain_consistency.sum()} rolling rainfall inconsistencies (rainfall_3d < rainfall_1d).")
    else:
        print("  [OK] Rolling cumulative rainfall consistency verified (rainfall_3d >= rainfall_1d).")
        
    # Wind speed and gust bounds
    wind_violation = (df['wind_speed'] < 0) | (df['wind_gust'] < df['wind_speed'])
    if wind_violation.sum() > 0:
        warnings.append(f"Found {wind_violation.sum()} wind gust < wind speed occurrences.")
    else:
        print("  [OK] Wind physical bounds verified (wind_gust >= wind_speed >= 0).")
        
    # Surface pressure in normal atmospheric range
    pressure_violation = (df['surface_pressure'] < 850) | (df['surface_pressure'] > 1080)
    if pressure_violation.sum() > 0:
        errors.append(f"Found {pressure_violation.sum()} atmospheric pressure range violations.")
    else:
        print("  [OK] Atmospheric surface pressure bounds verified (850 to 1080 hPa).")
        
    # Soil moisture bounds (10% to 100%)
    sm_violation = (df['soil_moisture'] < 10) | (df['soil_moisture'] > 100)
    if sm_violation.sum() > 0:
        errors.append(f"Found {sm_violation.sum()} soil moisture range violations.")
    else:
        print("  [OK] Soil moisture bounds verified (10% <= soil_moisture <= 100%).")
        
    # Real data provenance verification
    real_check = df['is_real'].all()
    if not real_check:
        errors.append("Non-real data detected in master real dataset.")
    else:
        print("  [OK] Strict Real Data Provenance verified (100% real records).")
        
    print("\n--- VALIDATION SUMMARY ---")
    if warnings:
        print(f"Warnings: {warnings}")
    if errors:
        print(f"[FAILED] Validation errors encountered: {errors}")
        return False
        
    print("[PASSED] Master dataset passed all meteorological and data quality checks.\n")
    return True

if __name__ == "__main__":
    validate_master_dataset()
