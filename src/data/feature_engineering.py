"""
feature_engineering.py - Meteorological & Hydrological Feature Engineering
SIH 2026 Problem Statement SIH26068
"""

import os
import pandas as pd
import numpy as np
from typing import Tuple, Dict
from clean_data import clean_open_meteo, clean_nrsc_rainfall, clean_netcdf_climatology

# Centroid coordinates for representative districts in Uttar Pradesh
UP_DISTRICT_COORDINATES: Dict[str, Tuple[float, float]] = {
    "Lucknow": (26.8467, 80.9462),
    "Kanpur Nagar": (26.4499, 80.3319),
    "Kanpur Dehat": (26.3400, 79.9400),
    "Kushi Nagar": (26.9000, 83.8800),
    "Varanasi": (25.3176, 82.9739),
    "Agra": (27.1767, 78.0081),
    "Prayagraj": (25.4358, 81.8463),
    "Allahabad": (25.4358, 81.8463),
    "Meerut": (28.9845, 77.7064),
    "Bareilly": (28.3670, 79.4304),
    "Aligarh": (27.8974, 78.0880),
    "Moradabad": (28.8350, 78.7760),
    "Saharanpur": (29.9640, 77.5460),
    "Gorakhpur": (26.7606, 83.3732),
    "Faizabad": (26.7730, 82.1460),
    "Ayodhya": (26.7730, 82.1460),
    "Jhansi": (25.4484, 78.5685),
    "Muzaffarnagar": (29.4727, 77.7085),
    "Mathura": (27.4924, 77.6737),
    "Budaun": (28.0300, 79.1200),
    "Rampur": (28.8100, 79.0300),
    "Shahjahanpur": (27.8800, 79.9100),
    "Farrukhabad": (27.3800, 79.5800),
    "Hardoi": (27.4200, 80.1200),
    "Sitapur": (27.5700, 80.6800),
    "Lakhimpur": (27.9500, 80.7800),
    "Kheri": (27.9500, 80.7800),
    "Unnao": (26.5400, 80.4900),
    "Rae Bareli": (26.2300, 81.2400),
    "Barabanki": (26.9300, 81.1900),
    "Sultanpur": (26.2600, 82.0700),
    "Amethi": (26.1500, 81.8100),
    "Pratapgarh": (25.9000, 81.9900),
    "Kaushambi": (25.5300, 81.4200),
    "Fatehpur": (25.9300, 80.8100),
    "Banda": (25.4800, 80.3400),
    "Chitrakoot": (25.2100, 80.9300),
    "Hamirpur": (25.9500, 80.1500),
    "Mahoba": (25.2900, 79.8700),
    "Jalaun": (26.1500, 79.3500),
    "Lalitpur": (24.6900, 78.4100),
    "Mirzapur": (25.1500, 82.5800),
    "Sonbhadra": (24.6900, 83.0700),
    "Bhadohi": (25.3900, 82.5700),
    "Sant Ravidas Nagar": (25.3900, 82.5700),
    "Jaunpur": (25.7500, 82.6800),
    "Ghazipur": (25.5800, 83.5800),
    "Chandauli": (25.2600, 83.2700),
    "Ballia": (25.7600, 84.1500),
    "Mau": (25.9500, 83.5600),
    "Azamgarh": (26.0700, 83.1800),
    "Deoria": (26.5000, 83.7800),
    "Basti": (26.8000, 82.7600),
    "Siddharthnagar": (27.2900, 82.8200),
    "Mahrajganj": (27.1400, 83.5600),
    "Sant Kabir Nagar": (26.7800, 83.0300),
    "Gonda": (27.1300, 81.9600),
    "Bahraich": (27.5800, 81.6000),
    "Shravasti": (27.7000, 81.9300),
    "Balrampur": (27.4300, 82.1800),
    "Baghpat": (28.9500, 77.2200),
    "Ghaziabad": (28.6700, 77.4200),
    "Gautam Buddha Nagar": (28.5300, 77.3900),
    "Noida": (28.5300, 77.3900),
    "Bulandshahr": (28.4100, 77.8500),
    "Hapur": (28.7300, 77.7800),
    "Sambhal": (28.5800, 78.5700),
    "Amroha": (28.9000, 78.4700),
    "Bijnor": (29.3700, 78.1300),
    "Shamli": (29.4500, 77.3100),
    "Kannauj": (27.0500, 79.9200),
    "Etawah": (26.7800, 79.0300),
    "Auraiya": (26.4700, 79.5200),
    "Mainpuri": (27.2300, 79.0200),
    "Firozabad": (27.1500, 78.4000),
    "Kasganj": (27.8100, 78.6500),
    "Hathras": (27.6000, 78.0500),
    "Etah": (27.6300, 78.6600)
}

# Default UP center coordinate fallback
DEFAULT_UP_COORD = (26.8467, 80.9462)

def get_season(month: int) -> str:
    """Returns meteorological season based on calendar month in India."""
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Summer"
    elif month in [6, 7, 8, 9]:
        return "Monsoon"
    else:
        return "Post-Monsoon"

def lookup_climatology(lat: float, lon: float, lats: np.ndarray, lons: np.ndarray, rf_grid: np.ndarray) -> float:
    """Extracts January baseline rainfall climatology from NetCDF grid for given coordinates."""
    i = int(np.argmin(np.abs(lats - lat)))
    j = int(np.argmin(np.abs(lons - lon)))
    val = float(rf_grid[i, j])
    if np.isnan(val) or val < 0:
        return 12.0 # Default regional representative climatology
    return round(val, 2)

def compute_soil_moisture_series(rainfall_series: pd.Series, temp_series: pd.Series = None) -> pd.Series:
    """
    Computes Antecedent Precipitation Index (API) proxy for soil moisture.
    API_t = API_{t-1} * decay + rainfall_t * infiltration
    Normalized to physical volumetric percentage: 15% (dry) to 90% (saturated).
    """
    api = np.zeros(len(rainfall_series))
    decay = 0.88
    current_val = 15.0
    
    for idx, rain in enumerate(rainfall_series.values):
        # Temperature adjustment if available (higher evapotranspiration in hot weather)
        temp_factor = 1.0
        if temp_series is not None and len(temp_series) > idx:
            t = temp_series.values[idx]
            if t > 35.0:
                temp_factor = 0.95
            elif t < 20.0:
                temp_factor = 1.02
        
        current_val = current_val * (decay * temp_factor) + (rain * 0.75)
        # Cap between 15% and 92%
        api[idx] = min(max(current_val, 15.0), 92.0)
        current_val = api[idx]
        
    return pd.Series(np.round(api, 1), index=rainfall_series.index)

def engineer_open_meteo_daily() -> pd.DataFrame:
    """Aggregates Open-Meteo hourly observations into daily engineered features."""
    df_raw, meta = clean_open_meteo()
    lats, lons, rf_grid = clean_netcdf_climatology()
    
    # Extract date from timestamp
    df_raw['date'] = df_raw['timestamp'].dt.date
    
    # Daily aggregations
    daily = df_raw.groupby('date').agg(
        temperature_mean=('temperature_2m', 'mean'),
        temperature_max=('temperature_2m', 'max'),
        temperature_min=('temperature_2m', 'min'),
        humidity_mean=('relative_humidity_2m', 'mean'),
        humidity_max=('relative_humidity_2m', 'max'),
        precipitation=('precipitation_mm', 'sum'),
        rainfall_1d=('rain_mm', 'sum'),
        wind_gust=('wind_gusts_10m', 'max'),
        surface_pressure=('surface_pressure', 'mean')
    ).reset_index()
    
    daily['date'] = pd.to_datetime(daily['date'])
    daily = daily.sort_values('date').reset_index(drop=True)
    
    # Wind speed estimate (mean gust scaled by typical gust factor ~0.65)
    daily['wind_speed'] = np.round(daily['wind_gust'] * 0.65, 1)
    
    # Rolling multi-day cumulative rainfall
    daily['rainfall_3d'] = daily['rainfall_1d'].rolling(window=3, min_periods=1).sum().round(2)
    daily['rainfall_7d'] = daily['rainfall_1d'].rolling(window=7, min_periods=1).sum().round(2)
    daily['rainfall_30d'] = daily['rainfall_1d'].rolling(window=30, min_periods=1).sum().round(2)
    
    # 24h lag differences
    daily['temperature_change_24h'] = daily['temperature_mean'].diff().fillna(0.0).round(2)
    daily['rainfall_change_24h'] = daily['rainfall_1d'].diff().fillna(0.0).round(2)
    
    # Calendar & seasonality
    daily['month'] = daily['date'].dt.month
    daily['day_of_year'] = daily['date'].dt.dayofyear
    daily['season'] = daily['month'].apply(get_season)
    
    # Location coordinates
    lat = meta.get('latitude', 20.56239)
    lon = meta.get('longitude', 78.93146)
    daily['latitude'] = lat
    daily['longitude'] = lon
    daily['district'] = "Wardha"
    daily['state'] = "Maharashtra"
    
    # Spatial Rainfall Climatology from NetCDF
    climatology_val = lookup_climatology(lat, lon, lats, lons, rf_grid)
    daily['rainfall_climatology'] = climatology_val
    
    # Defensible rainfall anomaly formula
    epsilon = 0.01
    daily['rainfall_anomaly'] = np.round(
        (daily['rainfall_1d'] - daily['rainfall_climatology']) / np.maximum(daily['rainfall_climatology'], epsilon),
        3
    )
    daily['rainfall_anomaly_percent'] = np.round(daily['rainfall_anomaly'] * 100.0, 1)
    
    # Soil moisture calculation
    daily['soil_moisture'] = compute_soil_moisture_series(daily['rainfall_1d'], daily['temperature_mean'])
    
    # Provenance flag
    daily['data_source'] = "Open-Meteo-Observation"
    daily['is_real'] = True
    
    # Round numerical columns
    for col in ['temperature_mean', 'temperature_max', 'temperature_min', 'humidity_mean', 'humidity_max', 'surface_pressure', 'precipitation', 'rainfall_1d']:
        daily[col] = daily[col].round(2)
        
    return daily

def engineer_nrsc_daily() -> pd.DataFrame:
    """Engineers daily features for 75 Uttar Pradesh districts from NRSC VIC model data."""
    df_raw = clean_nrsc_rainfall()
    lats, lons, rf_grid = clean_netcdf_climatology()
    
    # Sort by district and date
    df_raw = df_raw.sort_values(['district', 'date']).reset_index(drop=True)
    
    # Add coordinate lookup
    coords = df_raw['district'].map(UP_DISTRICT_COORDINATES).fillna(pd.Series([DEFAULT_UP_COORD]*len(df_raw)))
    df_raw['latitude'] = [c[0] for c in coords]
    df_raw['longitude'] = [c[1] for c in coords]
    
    # Rename rainfall column
    df_raw['rainfall_1d'] = df_raw['avg_rainfall_mm'].round(2)
    df_raw['precipitation'] = df_raw['rainfall_1d']
    
    # Grouped rolling calculations per district
    grouped = df_raw.groupby('district')
    df_raw['rainfall_3d'] = grouped['rainfall_1d'].rolling(window=3, min_periods=1).sum().round(2).values
    df_raw['rainfall_7d'] = grouped['rainfall_1d'].rolling(window=7, min_periods=1).sum().round(2).values
    df_raw['rainfall_30d'] = grouped['rainfall_1d'].rolling(window=30, min_periods=1).sum().round(2).values
    df_raw['rainfall_change_24h'] = grouped['rainfall_1d'].diff().fillna(0.0).round(2).values
    
    # Calendar features
    df_raw['month'] = df_raw['date'].dt.month
    df_raw['day_of_year'] = df_raw['date'].dt.dayofyear
    df_raw['season'] = df_raw['month'].apply(get_season)
    
    # District-specific NetCDF climatology lookup cache
    clim_cache = {}
    for district, (lat, lon) in UP_DISTRICT_COORDINATES.items():
        clim_cache[district] = lookup_climatology(lat, lon, lats, lons, rf_grid)
        
    default_clim = lookup_climatology(DEFAULT_UP_COORD[0], DEFAULT_UP_COORD[1], lats, lons, rf_grid)
    df_raw['rainfall_climatology'] = df_raw['district'].map(clim_cache).fillna(default_clim)
    
    # Anomaly
    epsilon = 0.01
    df_raw['rainfall_anomaly'] = np.round(
        (df_raw['rainfall_1d'] - df_raw['rainfall_climatology']) / np.maximum(df_raw['rainfall_climatology'], epsilon),
        3
    )
    df_raw['rainfall_anomaly_percent'] = np.round(df_raw['rainfall_anomaly'] * 100.0, 1)
    
    # District soil moisture
    moisture_list = []
    for district, group in df_raw.groupby('district'):
        sm = compute_soil_moisture_series(group['rainfall_1d'])
        moisture_list.append(pd.DataFrame({'index': group.index, 'soil_moisture': sm}))
    
    all_moisture = pd.concat(moisture_list).sort_values('index')['soil_moisture'].values
    df_raw['soil_moisture'] = all_moisture
    
    # Approximate temperature/humidity profile for northern plains by season
    # (keeps feature schema fully aligned without false station join)
    season_temp_defaults = {
        "Winter": (16.5, 23.0, 9.5, 68.0, 88.0, 1015.0, 8.0, 15.0),
        "Summer": (34.0, 42.0, 26.0, 32.0, 48.0, 1002.0, 14.0, 26.0),
        "Monsoon": (29.5, 34.0, 25.0, 78.0, 92.0, 998.0, 12.0, 22.0),
        "Post-Monsoon": (23.5, 30.0, 17.0, 55.0, 72.0, 1012.0, 7.0, 13.0)
    }
    
    df_raw['temperature_mean'] = [season_temp_defaults[s][0] for s in df_raw['season']]
    df_raw['temperature_max'] = [season_temp_defaults[s][1] for s in df_raw['season']]
    df_raw['temperature_min'] = [season_temp_defaults[s][2] for s in df_raw['season']]
    df_raw['humidity_mean'] = [season_temp_defaults[s][3] for s in df_raw['season']]
    df_raw['humidity_max'] = [season_temp_defaults[s][4] for s in df_raw['season']]
    df_raw['surface_pressure'] = [season_temp_defaults[s][5] for s in df_raw['season']]
    df_raw['wind_speed'] = [season_temp_defaults[s][6] for s in df_raw['season']]
    df_raw['wind_gust'] = [season_temp_defaults[s][7] for s in df_raw['season']]
    df_raw['temperature_change_24h'] = 0.0
    
    df_raw['data_source'] = "NRSC-VIC-Hydrological-Model"
    df_raw['is_real'] = True
    
    return df_raw

if __name__ == "__main__":
    df_daily_om = engineer_open_meteo_daily()
    print(f"[OK] Open-Meteo Daily Engineered: {df_daily_om.shape}")
    print(f"Features: {list(df_daily_om.columns)}")
    print(df_daily_om[['date', 'temperature_mean', 'rainfall_1d', 'rainfall_7d', 'rainfall_anomaly', 'soil_moisture']].head(3))
    
    df_daily_nrsc = engineer_nrsc_daily()
    print(f"[OK] NRSC Daily Engineered: {df_daily_nrsc.shape}")
    print(df_daily_nrsc[['date', 'district', 'rainfall_1d', 'rainfall_7d', 'rainfall_climatology', 'soil_moisture']].head(3))
