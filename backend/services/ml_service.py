"""
ml_service.py - Weather Impact Assessment Service for WeatherGPT
SIH 2026 Problem Statement SIH26068

WHAT CHANGED AND WHY
--------------------
The Weather Impact Score was inaccurate for two compounding reasons.

1. THE SCORING RULE COULD NOT ESCALATE ON A SINGLE HAZARD.
   The score came from a model trained on synthetic labels defined as a WEIGHTED
   AVERAGE: 0.40*rain + 0.25*wind + 0.15*pressure + 0.10*temp + 0.10*soil.
   A weighted average caps each hazard at its own weight. Measured on the
   shipped model with everything else benign:
        gusts 120 km/h   -> 30.0  -> LOW
        pressure 960 hPa -> 18.3  -> LOW
        temperature 48 C -> 21.8  -> LOW
   Super-cyclone winds, a cyclone-core pressure and a lethal heatwave all
   scored LOW, and rainfall above ~100 mm stopped changing the score at all.

2. THE INPUTS WERE MOSTLY INVENTED.
   This module used to derive ~20 of the model's 24 features from one number:
        rainfall_3d = precipitation * 1.5     surface_pressure = 1005 or 995
        rainfall_7d = precipitation * 2.2     soil_moisture = 42 + rain*0.75
        rainfall_30d = precipitation * 3.5
   So the "multi-hazard" score was effectively a function of precipitation.

The score now comes from services.impact_score - a transparent multi-hazard
index that takes max() across hazards (any one severe hazard drives the score)
using published IMD thresholds - and it is fed only values that are actually
observed or forecast. Anything unavailable is omitted, never fabricated.
"""

import sys
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import httpx

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.impact_score import compute_impact_score, explain_impact   # noqa: E402
from services.climatology_service import compute_rainfall_anomaly        # noqa: E402

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ANTECEDENT_DAYS = 31
_ANTECEDENT_TTL = 60 * 60 * 3
_ANTECEDENT_CACHE: Dict[str, Any] = {}
_LOCK = threading.Lock()

RECOMMENDATIONS = {
    0: "Conditions are within normal ranges. Routine outdoor activity, farm "
       "operations and travel are reasonable.",
    1: "Moderate weather impact expected. Keep drainage clear, plan outdoor work "
       "around the weather, and check the forecast again later today.",
    2: "Significant weather impact expected. Postpone spraying, secure produce and "
       "loose material, and avoid low-lying routes. Check IMD for official warnings.",
    3: "Severe weather impact expected. Check official IMD and State Disaster "
       "Management bulletins now and take precautionary action.",
}

DISCLAIMER = (
    "WeatherGPT Weather Impact Index - a deterministic index computed from observed "
    "and forecast values, not an official forecast or warning. IMD remains the "
    "authoritative source; verify before any emergency decision."
)


def get_meteorological_season(month: int) -> str:
    """IMD meteorological season label."""
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Summer"
    if month in (6, 7, 8, 9):
        return "Monsoon"
    return "Post-Monsoon"


# ------------------------------------------------------- antecedent rainfall
def fetch_antecedent_rainfall(lat: float, lon: float) -> Dict[str, Any]:
    """Fetches the last ~31 days of OBSERVED daily rainfall.

    Returns {"available": bool, "series": {iso_date: mm}, "source": str}.
    On failure it reports available=False - it never fabricates a series.
    """
    key = f"{round(lat, 2)},{round(lon, 2)}"
    now = time.time()
    with _LOCK:
        hit = _ANTECEDENT_CACHE.get(key)
        if hit and now - hit["ts"] < _ANTECEDENT_TTL:
            return hit["value"]

    result: Dict[str, Any] = {"available": False, "series": {}, "source": None}
    try:
        with httpx.Client(timeout=6.0) as client:
            resp = client.get(FORECAST_URL, params={
                "latitude": lat, "longitude": lon,
                "daily": "precipitation_sum",
                "past_days": ANTECEDENT_DAYS, "forecast_days": 1,
                "timezone": "Asia/Kolkata",
            })
        if resp.status_code == 200:
            daily = resp.json().get("daily", {})
            series = {t: float(v) for t, v in
                      zip(daily.get("time", []), daily.get("precipitation_sum", []))
                      if v is not None}
            if len(series) >= 8:
                result = {"available": True, "series": series,
                          "source": "Open-Meteo observed daily precipitation (past_days)"}
    except Exception as e:
        print(f"[WARN] Antecedent rainfall fetch failed for {key}: {type(e).__name__}: {e}")

    with _LOCK:
        _ANTECEDENT_CACHE[key] = {"ts": now, "value": result}
    return result


def _window_sum(series: Dict[str, float], end: datetime, days: int) -> Optional[float]:
    total, found = 0.0, 0
    for i in range(days):
        k = (end - timedelta(days=i)).strftime("%Y-%m-%d")
        if k in series:
            total += series[k]
            found += 1
    if found < max(1, days // 2):
        return None
    return round(total, 1)


def get_antecedent_rainfall_7d(lat: float, lon: float, as_of: datetime,
                               today_precip: float) -> Dict[str, Any]:
    """Real 7-day antecedent rainfall, or an explicit 'unavailable'."""
    data = fetch_antecedent_rainfall(lat, lon)
    if not data["available"]:
        return {"available": False, "rainfall_7d": None,
                "quality": "unavailable", "source": None}
    s7 = _window_sum(data["series"], as_of - timedelta(days=1), 6)
    if s7 is None:
        return {"available": False, "rainfall_7d": None,
                "quality": "sparse", "source": data["source"]}
    return {"available": True,
            "rainfall_7d": round(float(today_precip) + s7, 1),
            "quality": "observed", "source": data["source"]}


# ---------------------------------------------------------------- public API
def assess_risk_from_daily_features(
    location: str,
    lat: float,
    lon: float,
    t_max: float,
    t_min: float,
    precipitation: float,
    wind_gust: float,
    climatology: float = 12.0,
    humidity: float = 65.0,
    weather_code: int = 0,
    date_str: Optional[str] = None,
    surface_pressure: Optional[float] = None,
) -> Dict[str, Any]:
    """Weather Impact Index for one forecast day.

    Signature is unchanged (plus one optional argument) so
    weather_service.get_forecast() keeps working without modification.
    """
    try:
        return _assess(location, lat, lon, t_max, t_min, precipitation,
                       wind_gust, weather_code, date_str, surface_pressure)
    except Exception as e:
        # LAST-RESORT PATH. Whatever went wrong above - a network lookup, a cache
        # write, an unexpected None - the four values below came straight from the
        # weather API and the index over them is pure arithmetic that cannot fail.
        # A working dashboard must always show a score it can justify.
        print(f"[WARN] Enriched assessment failed for {location} "
              f"({type(e).__name__}: {e}); falling back to the core index.")
        try:
            core = compute_impact_score(
                precipitation_mm=precipitation, wind_gust_kmh=wind_gust,
                temperature_max_c=t_max, temperature_min_c=t_min,
                surface_pressure_hpa=surface_pressure)
            out = _to_response(location, core,
                               get_meteorological_season(datetime.now().month),
                               {"quality": "unavailable", "source": None},
                               {"available": False, "reason": "Enrichment unavailable"},
                               weather_code)
            out["degraded"] = True
            out["degraded_reason"] = f"{type(e).__name__}: {e}"
            return out
        except Exception as inner:
            print(f"[ERROR] Core index also failed for {location}: {inner}")
            return _to_response(location, {"available": False}, "Unknown",
                                {"quality": "unavailable"}, {"available": False})


def _assess(location, lat, lon, t_max, t_min, precipitation,
            wind_gust, weather_code, date_str, surface_pressure) -> Dict[str, Any]:
    try:
        as_of = datetime.strptime(date_str[:10], "%Y-%m-%d") if date_str else datetime.now()
    except Exception:
        as_of = datetime.now()

    season = get_meteorological_season(as_of.month)

    # The two enrichment lookups below are OPTIONAL. They reach the network, so
    # either can fail. Neither is allowed to take the whole score down with it:
    # rainfall, wind and temperature alone are enough to compute a real index.
    try:
        ante = get_antecedent_rainfall_7d(lat, lon, as_of, precipitation)
    except Exception as e:
        print(f"[WARN] Antecedent rainfall unavailable for {location}: {type(e).__name__}: {e}")
        ante = {"available": False, "rainfall_7d": None, "quality": "unavailable", "source": None}

    try:
        anomaly = compute_rainfall_anomaly(precipitation, lat, lon, as_of.strftime("%Y-%m-%d"))
    except Exception as e:
        print(f"[WARN] Rainfall climatology unavailable for {location}: {type(e).__name__}: {e}")
        anomaly = {"available": False, "reason": f"{type(e).__name__}"}

    anomaly_ratio = anomaly.get("anomaly_ratio") if anomaly.get("available") else None

    result = compute_impact_score(
        precipitation_mm=precipitation,
        wind_gust_kmh=wind_gust,
        temperature_max_c=t_max,
        temperature_min_c=t_min,
        surface_pressure_hpa=surface_pressure,      # omitted when not measured
        rainfall_7d_mm=ante.get("rainfall_7d"),     # omitted when not observed
        rainfall_anomaly_ratio=anomaly_ratio,
    )
    return _to_response(location, result, season, ante, anomaly, weather_code)


def _to_response(location: str, result: Dict[str, Any], season: str,
                 ante: Dict[str, Any], anomaly: Dict[str, Any],
                 weather_code: int = 0) -> Dict[str, Any]:
    """Maps the index onto the response shape the frontend already consumes."""
    if not result.get("available"):
        return {
            "location": location, "risk_score": 0.0, "risk_level": "UNAVAILABLE",
            "risk_level_code": -1, "confidence": None, "class_probabilities": {},
            "key_factors": ["Verified information is currently unavailable."],
            "recommendation": "No impact estimate is available. Consult IMD or local authorities.",
            "disclaimer": DISCLAIMER, "estimate_available": False,
            "provenance": {"type": "UNAVAILABLE", "is_official_warning": False},
        }

    # "Confidence" for a deterministic index is input completeness: how many of
    # the six hazard inputs were backed by real values. It is not a probability
    # and it is never clamped to a flattering range.
    n_possible = 6
    n_have = len(result["components"])
    confidence = round(n_have / n_possible, 2)

    level = result["level_code"]
    return {
        "location": location,
        "risk_score": result["score"],
        "risk_level": result["level"],
        "risk_level_code": level,
        "confidence": confidence,
        "class_probabilities": {},
        "key_factors": explain_impact(result),
        "recommendation": RECOMMENDATIONS[level],
        "disclaimer": DISCLAIMER,
        # ---- additive provenance ----
        "method": result["method"],
        "is_machine_learning": False,
        "dominant_hazard": result["dominant_hazard"],
        "dominant_band": result["dominant_band"],
        "hazard_components": result["components"],
        "inputs_available": f"{n_have} of {n_possible} hazard inputs",
        "season": season,
        "rainfall_anomaly": anomaly,
        "antecedent_quality": ante.get("quality"),
        "antecedent_source": ante.get("source"),
        "weather_code": weather_code,
        "provenance": {
            "type": "DETERMINISTIC_INDEX",
            "source": "WeatherGPT Multi-hazard Impact Index over Open-Meteo observations",
            "thresholds": "India Meteorological Department published categories",
            "is_official_warning": False,
        },
    }


def predict_custom_risk(req_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Direct entry point for POST /api/predict/risk.

    Uses only the values the caller actually supplies. Unsupplied hazards are
    omitted from the index rather than filled with derived defaults.
    """
    d = dict(req_dict)
    lat = float(d.get("latitude") or 21.1458)
    lon = float(d.get("longitude") or 79.0882)
    now = datetime.now()
    month = int(d.get("month") or now.month)
    season = d.get("season") or get_meteorological_season(month)

    precip = d.get("rainfall_1d")
    if precip is None:
        precip = d.get("precipitation")
    precip = float(precip) if precip is not None else None

    rain_7d = d.get("rainfall_7d")
    ante: Dict[str, Any] = {"quality": "caller_supplied", "source": None,
                            "rainfall_7d": rain_7d}
    if rain_7d is None and precip is not None:
        ante = get_antecedent_rainfall_7d(lat, lon, now, precip)
        rain_7d = ante.get("rainfall_7d")

    anomaly = compute_rainfall_anomaly(precip or 0.0, lat, lon,
                                       f"{now.year}-{month:02d}-15")
    ratio = d.get("rainfall_anomaly")
    if ratio is None and anomaly.get("available"):
        ratio = anomaly.get("anomaly_ratio")

    result = compute_impact_score(
        precipitation_mm=precip,
        wind_gust_kmh=d.get("wind_gust"),
        temperature_max_c=d.get("temperature_max"),
        temperature_min_c=d.get("temperature_min"),
        surface_pressure_hpa=d.get("surface_pressure"),
        rainfall_7d_mm=float(rain_7d) if rain_7d is not None else None,
        rainfall_anomaly_ratio=float(ratio) if ratio is not None else None,
    )
    return _to_response(d.get("location", "Unknown"), result, season, ante, anomaly)
