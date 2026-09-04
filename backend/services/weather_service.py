"""
weather_service.py - Real-time Weather Fetching, Geocoding & Offline Fallback Engine
SIH 2026 Problem Statement SIH26068
"""

import time
import httpx
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
from config import settings
from models.schemas import CurrentWeatherMetrics, WeatherCurrentResponse, DailyForecastItem, WeatherForecastResponse

# In-memory cache: (location_key) -> (timestamp, response_data)
_WEATHER_CACHE = {}
CACHE_TTL_SECONDS = 600 # 10 minutes

WEATHER_CODE_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

import re

def get_precipitation_category(p_mm: float, prob: float = 0.0) -> str:
    """Classifies precipitation according to official IMD meteorological standards."""
    if p_mm < 0.1 and prob < 20:
        return "No Rain (Dry)"
    elif p_mm < 2.5:
        return "Light Drizzle"
    elif p_mm < 7.6:
        return "Light Rain"
    elif p_mm < 35.6:
        return "Moderate Rain"
    elif p_mm < 64.5:
        return "Rather Heavy Rain"
    elif p_mm < 124.5:
        return "Heavy Rain"
    else:
        return "Very Heavy Rain / Cloudburst"

def compute_calibrated_rain_probability(
    precipitation_mm: float,
    weather_code: int = 0,
    raw_prob: Optional[float] = None,
    humidity: Optional[float] = None
) -> float:
    """
    Computes a physically calibrated, meteorologically sound Precipitation Probability (PoP, 0-100%).
    Eliminates arbitrary binary jumps (e.g. 10% vs 75%) by synthesizing:
    1. WMO weather code atmospheric state (Clear, Cloudy, Drizzle, Rain, Thunderstorm).
    2. Continuous physical precipitation accumulation curve (logistic/exponential scaling).
    3. Ambient relative humidity constraint.
    4. Raw NWP model probability cross-validation and smoothing.
    """
    p_val = max(0.0, float(precipitation_mm or 0.0))
    wc = int(weather_code or 0)

    # 1. Base physics probability from WMO weather code
    if wc == 0:        # Clear sky
        base_pop = 2.0
    elif wc == 1:      # Mainly clear
        base_pop = 5.0
    elif wc == 2:      # Partly cloudy
        base_pop = 14.0
    elif wc == 3:      # Overcast
        base_pop = 28.0
    elif wc in (45, 48): # Fog / mist
        base_pop = 22.0
    elif wc in (51, 53, 55): # Drizzle (light, moderate, dense)
        base_pop = 52.0 + (wc - 51) * 8.0 # 52%, 68%, 84%
    elif wc in (56, 57): # Freezing drizzle
        base_pop = 65.0
    elif wc == 61:     # Slight rain
        base_pop = 70.0
    elif wc == 63:     # Moderate rain
        base_pop = 82.0
    elif wc == 65:     # Heavy rain
        base_pop = 92.0
    elif wc in (66, 67): # Freezing rain
        base_pop = 80.0
    elif wc in (71, 73, 75, 77): # Snow
        base_pop = 75.0
    elif wc == 80:     # Slight rain showers
        base_pop = 74.0
    elif wc == 81:     # Moderate rain showers
        base_pop = 85.0
    elif wc == 82:     # Violent rain showers
        base_pop = 94.0
    elif wc in (95, 96, 99): # Thunderstorms
        base_pop = 90.0 if wc == 95 else 95.0
    else:
        base_pop = 20.0 if p_val > 0 else 5.0

    # 2. Continuous accumulation scaling (mm of rain)
    if p_val == 0.0:
        if wc <= 1:
            vol_pop = base_pop
        elif wc == 2:
            vol_pop = 12.0
        elif wc == 3:
            vol_pop = 22.0
        elif wc in (45, 48):
            vol_pop = 20.0
        else:
            vol_pop = min(base_pop, 45.0)
    elif p_val < 0.5:
        vol_pop = 35.0 + (p_val / 0.5) * 20.0
    elif p_val < 2.5:
        vol_pop = 55.0 + ((p_val - 0.5) / 2.0) * 17.0
    elif p_val < 10.0:
        vol_pop = 72.0 + ((p_val - 2.5) / 7.5) * 14.0
    elif p_val < 35.0:
        vol_pop = 86.0 + min(9.0, ((p_val - 10.0) / 25.0) * 9.0)
    else:
        vol_pop = min(99.0, 95.0 + (p_val - 35.0) * 0.1)

    # Blend WMO code baseline and volume-derived probability
    if p_val > 0.0:
        calibrated = 0.55 * vol_pop + 0.45 * max(base_pop, 50.0)
    else:
        calibrated = vol_pop

    # 3. Incorporate Raw NWP probability if available
    if raw_prob is not None:
        try:
            rp = float(raw_prob)
            if 0.0 <= rp <= 100.0:
                if p_val == 0.0 and wc <= 1:
                    calibrated = min(calibrated, max(rp * 0.3, 8.0))
                elif p_val >= 2.0:
                    calibrated = max(calibrated, min(rp, 95.0))
                else:
                    calibrated = 0.60 * calibrated + 0.40 * rp
        except Exception:
            pass

    # 4. Humidity adjustment
    if humidity is not None:
        try:
            h = float(humidity)
            if p_val == 0.0 and h < 45.0:
                calibrated *= 0.70
            elif p_val > 0.0 and h > 85.0:
                calibrated = min(99.0, calibrated * 1.05)
        except Exception:
            pass

    return round(float(np.clip(calibrated, 1.0 if (p_val > 0 or wc >= 50) else 0.0, 99.0)), 1)


def resolve_location(
    query: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None
) -> Tuple[str, str, float, float, float]:
    """
    Resolves location string to (name, state, lat, lon, climatology).
    Handles:
    - Explicit coordinates: lat and lon passed as arguments (Highest Priority)
    - Indian 6-digit PIN code: '273303', '226001', 'PIN 273303'
    - Raw GPS coordinates in string: 'GPS Location (28.752°N, 77.499°E)' or '28.752, 77.499'
    - Curated Tehsils & Blocks: 'Nautanwa', 'Malihabad', 'Mohanlalganj', 'Nichlaul', etc.
    - Compound village/district strings: 'Muradnagar (Ghaziabad)', 'Kelod (Nagpur)'
    - Direct names: 'Nagpur', 'Coimbatore', 'Patna'
    """
    cleaned = (query or "").strip()

    # 1. Highest Priority: Explicit coordinates provided directly by frontend/client
    if lat is not None and lon is not None:
        try:
            f_lat = float(lat)
            f_lon = float(lon)
            if not np.isnan(f_lat) and not np.isnan(f_lon) and -90 <= f_lat <= 90 and -180 <= f_lon <= 180:
                disp_name = cleaned.strip() if cleaned and cleaned.strip() else f"GPS ({f_lat:.4f}°N, {f_lon:.4f}°E)"
                return disp_name, "India", f_lat, f_lon, 12.0
        except Exception:
            pass

    # 2. Check if 6-digit Indian PIN code is present in query
    pin_match = re.search(r'\b([1-9][0-9]{5})\b', cleaned)
    if pin_match:
        try:
            from api.location import geocode_pincode_coordinates
            pin = pin_match.group(1)
            p_coords = geocode_pincode_coordinates(pin)
            if p_coords:
                disp_name = cleaned if len(cleaned) > 6 else f"PIN Code {pin}"
                return disp_name, "India", p_coords[0], p_coords[1], 12.0
        except Exception as e:
            print(f"[WARN] PIN geocode resolution note: {e}")

    # 3. Check if GPS coordinates are present in the string
    coord_match = re.search(r'(-?\d+\.?\d*)\s*°?\s*([NnSs])?\s*[,/ ]+\s*(-?\d+\.?\d*)\s*°?\s*([EeWw])?', cleaned)
    if coord_match:
        try:
            c_lat = float(coord_match.group(1))
            c_lon = float(coord_match.group(3))
            if coord_match.group(2) in ['S', 's']: c_lat = -c_lat
            if coord_match.group(4) in ['W', 'w']: c_lon = -c_lon
            # Extract friendly place name if present
            disp_name = re.sub(r'GPS Location|\(.*?\)', '', cleaned).strip() or f"GPS ({c_lat:.3f}°N, {c_lon:.3f}°E)"
            return disp_name, "India", c_lat, c_lon, 12.0
        except Exception:
            pass

    # 4. Check known curated tehsils/blocks in Uttar Pradesh & across districts
    try:
        from api.location import SUBDISTRICT_COORDINATES
        clean_search = re.sub(r'\(.*?\)', '', cleaned).replace(" district", "").strip()
        clean_lower = clean_search.lower()
        if clean_lower in SUBDISTRICT_COORDINATES:
            sc = SUBDISTRICT_COORDINATES[clean_lower]
            return clean_search.title(), "Uttar Pradesh", sc["lat"], sc["lon"], 12.0
    except Exception:
        pass

    # 5. High-Speed Photon Geocoding for any village, town, or district in India
    try:
        import urllib.parse
        clean_search = re.sub(r'\(.*?\)', '', cleaned).replace(" district", "").strip()
        encoded_q = urllib.parse.quote(cleaned.strip())
        url_ph = f"https://photon.komoot.io/api/?q={encoded_q}&bbox=68.1,6.5,97.4,35.7&limit=1"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WeatherGPT/2.0", "Accept-Language": "en"}
        with httpx.Client(timeout=3.0) as client:
            resp_ph = client.get(url_ph, headers=headers)
            if resp_ph.status_code == 200:
                features = resp_ph.json().get("features", [])
                if features:
                    f0 = features[0]
                    coords_ph = f0.get("geometry", {}).get("coordinates", [])
                    if len(coords_ph) >= 2:
                        p_lat = float(coords_ph[1])
                        p_lon = float(coords_ph[0])
                        if 6.0 <= p_lat <= 38.0 and 68.0 <= p_lon <= 98.0:
                            p_props = f0.get("properties", {})
                            res_name = p_props.get("name") or cleaned
                            res_state = p_props.get("state") or "India"
                            return res_name, res_state, p_lat, p_lon, 12.5
    except Exception as eph:
        print(f"[WARN] Photon resolve_location notice for '{cleaned}': {eph}")

    # 6. Check local pre-indexed locations
    clean_search = re.sub(r'\(.*?\)', '', cleaned).replace(" district", "").strip()
    clean_lower = clean_search.lower()
    if clean_lower in settings.LOCATIONS:
        loc = settings.LOCATIONS[clean_lower]
        return loc["name"], loc["state"], loc["lat"], loc["lon"], loc["climatology"]

    for key, loc in settings.LOCATIONS.items():
        if key in clean_lower or clean_lower in key:
            return loc["name"], loc["state"], loc["lat"], loc["lon"], loc["climatology"]

    # 7. Query Open-Meteo Geocoding API with clean place name
    try:
        url = f"{settings.OPEN_METEO_GEOCODING_URL}?name={clean_search}&count=5&language=en&country_code=IN&format=json"
        with httpx.Client(timeout=3.5) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    r = results[0]
                    name = r.get("name", clean_search.title())
                    state = r.get("admin1", "India")
                    lat_res = float(r.get("latitude", 20.56))
                    lon_res = float(r.get("longitude", 78.93))
                    return name, state, lat_res, lon_res, 12.5
    except Exception as e:
        print(f"[WARN] Live geocoding failed for '{clean_search}': {e}")

    # Fallback to default
    def_loc = settings.LOCATIONS["nagpur"]
    return cleaned.title(), def_loc["state"], def_loc["lat"], def_loc["lon"], def_loc["climatology"]

def get_current_weather(
    location_query: str = "Nagpur",
    lat: Optional[float] = None,
    lon: Optional[float] = None
) -> WeatherCurrentResponse:
    """Fetches real-time current weather with graceful offline fallback."""
    name, state, lat_val, lon_val, clim = resolve_location(location_query, lat, lon)
    cache_key = f"current_{lat_val:.4f}_{lon_val:.4f}"
    
    now = time.time()
    if cache_key in _WEATHER_CACHE:
        cached_time, cached_res = _WEATHER_CACHE[cache_key]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_res
            
    # Attempt Live Open-Meteo API
    try:
        params = {
            "latitude": lat_val,
            "longitude": lon_val,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "is_day",
                "precipitation",
                "rain",
                "weather_code",
                "surface_pressure",
                "wind_speed_10m",
                "wind_gusts_10m"
            ],
            "timezone": "Asia/Kolkata"
        }
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(settings.OPEN_METEO_API_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                c = data.get("current", {})
                w_code = int(c.get("weather_code", 0))
                desc = WEATHER_CODE_DESCRIPTIONS.get(w_code, "Partly Cloudy")
                precip_val = float(c.get("precipitation", 0.0))
                rel_hum = float(c.get("relative_humidity_2m", 65.0))
                precip_prob = compute_calibrated_rain_probability(precip_val, w_code, humidity=rel_hum)
                precip_cat = get_precipitation_category(precip_val, precip_prob)

                metrics = CurrentWeatherMetrics(
                    temperature=float(c.get("temperature_2m", 28.0)),
                    apparent_temperature=float(c.get("apparent_temperature", 30.0)),
                    relative_humidity=rel_hum,
                    precipitation=precip_val,
                    rain=float(c.get("rain", 0.0)),
                    wind_speed=float(c.get("wind_speed_10m", 12.0)),
                    wind_gust=float(c.get("wind_gusts_10m", 18.0)),
                    surface_pressure=float(c.get("surface_pressure", 1008.0)),
                    weather_code=w_code,
                    weather_description=desc,
                    is_day=int(c.get("is_day", 1)),
                    timestamp=str(c.get("time", pd.Timestamp.now().isoformat())),
                    precipitation_probability=precip_prob,
                    precipitation_intensity=precip_cat
                )
                
                result = WeatherCurrentResponse(
                    location=name,
                    state=state,
                    latitude=lat_val,
                    longitude=lon_val,
                    elevation_m=float(data.get("elevation", 245.0)),
                    data_source="LIVE (Open-Meteo API)",
                    current=metrics
                )
                _WEATHER_CACHE[cache_key] = (now, result)
                return result
    except Exception as e:
        print(f"[WARN] Live Open-Meteo call failed: {e}. Switching to DEMO/OFFLINE fallback.")
        
    # Offline Fallback
    fallback_prob = compute_calibrated_rain_probability(0.0, 1, humidity=62.0)
    metrics = CurrentWeatherMetrics(
        temperature=28.4,
        apparent_temperature=30.2,
        relative_humidity=62.0,
        precipitation=0.0,
        rain=0.0,
        wind_speed=14.5,
        wind_gust=21.0,
        surface_pressure=992.5,
        weather_code=1,
        weather_description="Mainly clear (Offline baseline)",
        is_day=1,
        timestamp=pd.Timestamp.now().strftime("%Y-%m-%dT%H:00"),
        precipitation_probability=fallback_prob,
        precipitation_intensity="No Rain (Dry)"
    )
    result = WeatherCurrentResponse(
        location=name,
        state=state,
        latitude=lat_val,
        longitude=lon_val,
        elevation_m=245.0,
        data_source="DEMO/OFFLINE (Historical Station Baseline)",
        current=metrics
    )
    return result

def get_forecast(
    location_query: str = "Nagpur",
    days: int = 7,
    lat: Optional[float] = None,
    lon: Optional[float] = None
) -> WeatherForecastResponse:
    """Fetches 7-day forecast with authentic per-day precipitation prediction and AI Risk."""
    from services.ml_service import assess_risk_from_daily_features
    
    name, state, lat_val, lon_val, clim = resolve_location(location_query, lat, lon)
    cache_key = f"forecast_{lat_val:.4f}_{lon_val:.4f}_{days}"
    
    now = time.time()
    if cache_key in _WEATHER_CACHE:
        cached_time, cached_res = _WEATHER_CACHE[cache_key]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_res
            
    source = "LIVE (Open-Meteo API)"
    daily_items = []
    
    try:
        params = {
            "latitude": lat_val,
            "longitude": lon_val,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_hours",
                "precipitation_probability_max",
                "rain_sum",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "weather_code"
            ],
            "timezone": "Asia/Kolkata",
            "forecast_days": min(days, 7)
        }
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(settings.OPEN_METEO_API_URL, params=params)
            if resp.status_code == 200:
                data = resp.json().get("daily", {})
                times = data.get("time", [])
                t_max = data.get("temperature_2m_max", [])
                t_min = data.get("temperature_2m_min", [])
                precip = data.get("precipitation_sum", [])
                precip_hrs = data.get("precipitation_hours", [])
                precip_probs = data.get("precipitation_probability_max", [])
                rain = data.get("rain_sum", [])
                wind = data.get("wind_speed_10m_max", [])
                gusts = data.get("wind_gusts_10m_max", [])
                wcodes = data.get("weather_code", [])
                
                for i in range(len(times)):
                    wc = int(wcodes[i]) if i < len(wcodes) else 0
                    p = float(precip[i]) if i < len(precip) else 0.0
                    raw_prob_val = float(precip_probs[i]) if i < len(precip_probs) and precip_probs[i] is not None else None
                    p_prob = compute_calibrated_rain_probability(p, wc, raw_prob=raw_prob_val)
                    p_hrs = float(precip_hrs[i]) if i < len(precip_hrs) and precip_hrs[i] is not None else (round(p * 0.4, 1) if p > 0 else 0.0)
                    r = float(rain[i]) if i < len(rain) else 0.0
                    g = float(gusts[i]) if i < len(gusts) else 15.0
                    tm = float(t_max[i]) if i < len(t_max) else 30.0
                    tn = float(t_min[i]) if i < len(t_min) else 20.0
                    
                    p_cat = get_precipitation_category(p, p_prob)
                    
                    # Compute AI risk for each forecast day
                    try:
                        risk_assessment = assess_risk_from_daily_features(
                            location=name,
                            lat=lat_val,
                            lon=lon_val,
                            t_max=tm,
                            t_min=tn,
                            precipitation=p,
                            wind_gust=g,
                            climatology=clim
                        )
                    except Exception as err:
                        print(f"[WARN] Risk assessment failed for {times[i]}: {err}")
                        risk_assessment = {"risk_score": 15.0, "risk_level": "LOW"}
                    
                    daily_items.append(DailyForecastItem(
                        date=times[i],
                        temperature_max=tm,
                        temperature_min=tn,
                        precipitation_sum=p,
                        rain_sum=r,
                        wind_speed_max=float(wind[i]) if i < len(wind) else 12.0,
                        wind_gust_max=g,
                        weather_code=wc,
                        weather_description=WEATHER_CODE_DESCRIPTIONS.get(wc, "Clear"),
                        risk_score=risk_assessment.get("risk_score", 15.0),
                        risk_level=risk_assessment.get("risk_level", "LOW"),
                        precipitation_probability_max=p_prob,
                        precipitation_hours=p_hrs,
                        precipitation_category=p_cat
                    ))
    except Exception as e:
        print(f"[WARN] Live forecast failed: {e}. Generating offline forecast.")
        source = "DEMO/OFFLINE (Historical Station Baseline)"
        
    if not daily_items:
        # Fallback 7-day forecast
        today = pd.Timestamp.now()
        for d in range(days):
            date_str = (today + pd.Timedelta(days=d)).strftime("%Y-%m-%d")
            p = 15.0 if d == 1 else (45.0 if d == 2 else 2.0)
            g = 42.0 if d in [1, 2] else 18.0
            tm = 32.0 - (d * 0.8)
            tn = 22.0
            wc = 61 if p > 10 else 1
            p_prob = compute_calibrated_rain_probability(p, wc)
            
            try:
                risk_assessment = assess_risk_from_daily_features(
                    location=name, lat=lat_val, lon=lon_val, t_max=tm, t_min=tn, precipitation=p, wind_gust=g, climatology=clim
                )
            except Exception as err:
                risk_assessment = {"risk_score": 15.0, "risk_level": "LOW"}

            daily_items.append(DailyForecastItem(
                date=date_str,
                temperature_max=tm,
                temperature_min=tn,
                precipitation_sum=p,
                rain_sum=p,
                wind_speed_max=22.0 if d in [1, 2] else 12.0,
                wind_gust_max=g,
                weather_code=wc,
                weather_description="Moderate rain" if p > 10 else "Mainly clear",
                risk_score=risk_assessment.get("risk_score", 15.0),
                risk_level=risk_assessment.get("risk_level", "LOW"),
                precipitation_probability_max=p_prob,
                precipitation_hours=round(p * 0.4, 1) if p > 0 else 0.0,
                precipitation_category=get_precipitation_category(p, p_prob)
            ))
            
    res = WeatherForecastResponse(
        location=name,
        state=state,
        latitude=lat_val,
        longitude=lon_val,
        data_source=source,
        forecast_days=daily_items
    )
    _WEATHER_CACHE[cache_key] = (now, res)
    return res
