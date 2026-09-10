"""
cyclone_detect.py - Real-time low-pressure system detection for WeatherGPT
SIH 2026 Problem Statement SIH26068

WHAT THIS REPLACES
------------------
cyclone_service.get_active_cyclone_systems() returned two hardcoded dictionaries -
a fictional storm named 'DANA' at a fixed position with a typed-in forecast track
and a frozen timestamp. Nothing in it was observed.

WHAT THIS DOES
--------------
There is no free public API for live IMD cyclone bulletins. But the underlying
physics IS freely available: Open-Meteo serves mean-sea-level pressure and 10 m
wind on any coordinate, hourly, without an API key.

So instead of being told where a cyclone is, this module finds it:

  1. Scan a coarse grid across the Bay of Bengal and Arabian Sea.
  2. Locate local pressure minima that fall below the IMD low-pressure threshold.
  3. Merge nearby minima into a single system centre.
  4. Convert the pressure deficit into maximum sustained wind using the
     Atkinson-Holliday relation already implemented in cyclone_service.py, and
     classify with the IMD intensity bands already implemented there.
  5. Repeat the scan at forecast hours to trace where the centre is heading.

HONESTY
-------
Everything produced here is a MODEL ESTIMATE derived from a public forecast
model. It is never an official warning, and it says so in every payload. When no
grid point meets the threshold, the answer is "no active system detected" - not
an invented storm. Grid resolution puts centre position within roughly +/-100 km,
which is adequate for district-level risk and NOT adequate for a landfall-time
claim; the payload states this.
"""

import math
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

import httpx

from services.cyclone_service import calculate_wind_from_pressure, get_imd_category

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Basin scan windows. Coarse on purpose: ~2 degrees is enough to FIND a system,
# and keeps the whole scan inside a handful of requests.
BASINS = [
    {"name": "Bay of Bengal", "lat": (5.0, 23.0), "lon": (80.0, 95.0), "step": 2.0},
    {"name": "Arabian Sea", "lat": (5.0, 25.0), "lon": (55.0, 78.0), "step": 2.0},
]

# IMD: a low-pressure area is the weakest classified system. Below this we do not
# report anything, to avoid dressing up ordinary monsoon pressure as a "system".
LPA_THRESHOLD_HPA = 1004.0
MIN_PRESSURE_DEFICIT_HPA = 3.0      # centre must be this far below basin ambient
MERGE_RADIUS_KM = 300.0             # minima closer than this are one system
FORECAST_HOURS = [12, 24, 36, 48]

_CACHE: Dict[str, Any] = {}
_CACHE_TTL = 60 * 30                # half an hour; the model updates hourly
_LOCK = threading.Lock()
REQUEST_TIMEOUT = 25.0
MAX_POINTS_PER_REQUEST = 100


# ------------------------------------------------------------------ geometry
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def bearing_to_compass(lat1: float, lon1: float, lat2: float, lon2: float) -> str:
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(math.radians(lat2))
    x = (math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) -
         math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dl))
    deg = (math.degrees(math.atan2(y, x)) + 360) % 360
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[int((deg + 11.25) % 360 / 22.5)]


def _grid(basin: Dict[str, Any]) -> List[Tuple[float, float]]:
    pts = []
    lat0, lat1 = basin["lat"]
    lon0, lon1 = basin["lon"]
    step = basin["step"]
    la = lat0
    while la <= lat1 + 1e-9:
        lo = lon0
        while lo <= lon1 + 1e-9:
            pts.append((round(la, 3), round(lo, 3)))
            lo += step
        la += step
    return pts


# ----------------------------------------------------------------- fetching
def fetch_field(points: List[Tuple[float, float]],
                forecast_hours: int = 48) -> Optional[List[Dict[str, Any]]]:
    """Fetches pressure and wind for many coordinates.

    Open-Meteo accepts comma-separated latitude/longitude and returns one result
    object per coordinate. Returns None if the field cannot be retrieved - the
    caller must then report "unavailable", never guess.
    """
    out: List[Dict[str, Any]] = []
    for start in range(0, len(points), MAX_POINTS_PER_REQUEST):
        chunk = points[start:start + MAX_POINTS_PER_REQUEST]
        params = {
            "latitude": ",".join(str(p[0]) for p in chunk),
            "longitude": ",".join(str(p[1]) for p in chunk),
            "hourly": "pressure_msl,wind_speed_10m,wind_gusts_10m",
            "forecast_days": max(2, math.ceil(forecast_hours / 24) + 1),
            "timezone": "UTC",
        }
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                resp = client.get(FORECAST_URL, params=params)
            if resp.status_code != 200:
                print(f"[WARN] Cyclone field fetch HTTP {resp.status_code}")
                return None
            payload = resp.json()
            # A multi-coordinate request returns a list; a single one returns a dict.
            blocks = payload if isinstance(payload, list) else [payload]
            for (la, lo), blk in zip(chunk, blocks):
                hourly = blk.get("hourly") or {}
                out.append({
                    "lat": la, "lon": lo,
                    "time": hourly.get("time", []),
                    "pressure": hourly.get("pressure_msl", []),
                    "wind": hourly.get("wind_speed_10m", []),
                    "gust": hourly.get("wind_gusts_10m", []),
                })
        except Exception as e:
            print(f"[WARN] Cyclone field fetch failed: {type(e).__name__}: {e}")
            return None
    return out


# ---------------------------------------------------------------- detection
def _value_at(cell: Dict[str, Any], key: str, idx: int) -> Optional[float]:
    seq = cell.get(key) or []
    if idx < len(seq) and seq[idx] is not None:
        return float(seq[idx])
    return None


def find_minima(cells: List[Dict[str, Any]], idx: int) -> List[Dict[str, Any]]:
    """Finds local pressure minima at hour index `idx`."""
    valued = []
    for c in cells:
        p = _value_at(c, "pressure", idx)
        if p is not None:
            valued.append({"lat": c["lat"], "lon": c["lon"], "pressure": p,
                           "gust": _value_at(c, "gust", idx) or 0.0,
                           "wind": _value_at(c, "wind", idx) or 0.0})
    if len(valued) < 8:
        return []

    pressures = sorted(v["pressure"] for v in valued)
    # Ambient = upper quartile of the basin field, a robust "surrounding" value.
    ambient = pressures[int(len(pressures) * 0.75)]

    minima = []
    for v in valued:
        if v["pressure"] > LPA_THRESHOLD_HPA:
            continue
        if ambient - v["pressure"] < MIN_PRESSURE_DEFICIT_HPA:
            continue
        # Must be the lowest point among its near neighbours.
        neighbours = [o for o in valued
                      if o is not v and haversine_km(v["lat"], v["lon"], o["lat"], o["lon"]) <= 320]
        if neighbours and min(o["pressure"] for o in neighbours) < v["pressure"]:
            continue
        v = dict(v)
        v["ambient"] = ambient
        minima.append(refine_centre(v, valued))
    return minima


def refine_centre(m: Dict[str, Any], valued: List[Dict[str, Any]],
                  radius_km: float = 350.0) -> Dict[str, Any]:
    """Refines a centre to sub-grid precision with a pressure-weighted centroid.

    Snapping the centre to the nearest grid node quantises position to the grid
    step (~220 km at 2 degrees), which makes a moving system appear stationary
    between forecast hours. Weighting the surrounding nodes by how far below
    ambient they sit recovers a smooth, continuous position.
    """
    num_lat = num_lon = wsum = 0.0
    for o in valued:
        d = haversine_km(m["lat"], m["lon"], o["lat"], o["lon"])
        if d > radius_km:
            continue
        w = max(0.0, m["ambient"] - o["pressure"]) ** 2      # emphasise the core
        if w <= 0:
            continue
        num_lat += o["lat"] * w
        num_lon += o["lon"] * w
        wsum += w
    if wsum <= 0:
        return m
    out = dict(m)
    out["lat"] = round(num_lat / wsum, 3)
    out["lon"] = round(num_lon / wsum, 3)
    out["grid_lat"], out["grid_lon"] = m["lat"], m["lon"]
    return out


def _merge(minima: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collapses minima that belong to the same system."""
    merged: List[Dict[str, Any]] = []
    for m in sorted(minima, key=lambda x: x["pressure"]):
        if any(haversine_km(m["lat"], m["lon"], k["lat"], k["lon"]) < MERGE_RADIUS_KM
               for k in merged):
            continue
        merged.append(m)
    return merged


def _sea_name(lat: float, lon: float) -> str:
    return "Bay of Bengal" if lon >= 78.0 else "Arabian Sea"


def _build_system(centre: Dict[str, Any], cells: List[Dict[str, Any]],
                  times: List[str], idx0: int) -> Dict[str, Any]:
    """Assembles one system, including a track from FORECAST pressure fields."""
    wind = calculate_wind_from_pressure(centre["pressure"], centre["ambient"])
    category = get_imd_category(wind["vmax_kmh"])
    basin = _sea_name(centre["lat"], centre["lon"])

    # Track: re-find the nearest minimum at each forecast hour.
    track = [{
        "hour": "Now",
        "lat": centre["lat"], "lon": centre["lon"],
        "pressure_hpa": round(centre["pressure"], 1),
        "intensity": f"{category['title']} ({wind['vmax_kmh']:.0f} km/h)",
    }]
    prev = centre
    for h in FORECAST_HOURS:
        j = idx0 + h
        if j >= len(times):
            break
        future = find_minima(cells, j)
        if not future:
            continue
        near = min(future, key=lambda m: haversine_km(prev["lat"], prev["lon"], m["lat"], m["lon"]))
        if haversine_km(prev["lat"], prev["lon"], near["lat"], near["lon"]) > 600:
            break                      # too far to be the same system
        w = calculate_wind_from_pressure(near["pressure"], near["ambient"])
        track.append({
            "hour": f"+{h}h",
            "lat": near["lat"], "lon": near["lon"],
            "pressure_hpa": round(near["pressure"], 1),
            "intensity": f"{get_imd_category(w['vmax_kmh'])['title']} ({w['vmax_kmh']:.0f} km/h)",
        })
        prev = near

    movement = None
    if len(track) >= 2:
        a, b = track[0], track[1]
        d = haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
        hours = int(track[1]["hour"].strip("+h"))
        movement = {
            "direction": bearing_to_compass(a["lat"], a["lon"], b["lat"], b["lon"]),
            "speed_kmh": round(d / hours, 1) if hours else None,
        }

    deficit = wind["pressure_deficit_hpa"]
    rings = [
        {"hpa": round(centre["pressure"] + deficit * f, 0),
         "radius_km": r, "color": c, "label": f"{round(centre['pressure'] + deficit * f)} hPa"}
        for f, r, c in [(0.25, 60, "#be123c"), (0.5, 150, "#e11d48"),
                        (0.75, 280, "#f97316"), (1.0, 450, "#3b82f6")]
    ]

    return {
        "id": f"{'BOB' if basin == 'Bay of Bengal' else 'ARB'}-{abs(centre['lat']):.0f}{abs(centre['lon']):.0f}",
        "name": f"{category['title']} over the {basin}",
        "basin": basin,
        "status": "DETECTED_FROM_PRESSURE_FIELD",
        "central_pressure_hpa": round(centre["pressure"], 1),
        "ambient_pressure_hpa": round(centre["ambient"], 1),
        "pressure_deficit_hpa": deficit,
        "vmax_kmh": wind["vmax_kmh"],
        "gust_kmh": round(max(wind["gust_kmh"], centre.get("gust", 0.0)), 1),
        "observed_gust_kmh": round(centre.get("gust", 0.0), 1),
        "category": category,
        "estimated_surge_m": wind["estimated_surge_m"],
        "current_position": {
            "lat": centre["lat"], "lon": centre["lon"],
            "location_name": f"{basin} ({centre['lat']:.1f}N, {centre['lon']:.1f}E)",
        },
        "movement": movement,
        "forecast_track": track,
        "isobar_rings": rings,
        "position_uncertainty_km": 75,
        "provenance": {
            "type": "MODEL_ESTIMATE",
            "source": "Open-Meteo mean-sea-level pressure and 10 m wind fields",
            "method": "Grid scan for local pressure minima; Atkinson-Holliday wind-pressure "
                      "relation; IMD intensity classification",
            "is_official_warning": False,
        },
    }


# -------------------------------------------------------------- public API
def detect_active_systems(force: bool = False) -> Dict[str, Any]:
    """Scans both basins and returns any detected low-pressure systems."""
    now = time.time()
    with _LOCK:
        hit = _CACHE.get("systems")
        if hit and not force and now - hit["ts"] < _CACHE_TTL:
            return hit["value"]

    points: List[Tuple[float, float]] = []
    for b in BASINS:
        points.extend(_grid(b))

    cells = fetch_field(points)
    if cells is None:
        result = {
            "available": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_systems_count": 0,
            "systems": [],
            "message": "Live pressure field is unavailable, so cyclone detection cannot run. "
                       "No cyclone information is being shown rather than an estimate.",
            "data_source": "Open-Meteo (unreachable)",
            "is_official_warning": False,
        }
        with _LOCK:
            _CACHE["systems"] = {"ts": now, "value": result}
        return result

    times = next((c["time"] for c in cells if c.get("time")), [])
    # Index of the hour closest to now.
    idx0 = 0
    if times:
        target = datetime.now(timezone.utc).replace(tzinfo=None)
        best = None
        for i, t in enumerate(times):
            try:
                dt = datetime.fromisoformat(t)
            except Exception:
                continue
            gap = abs((dt - target).total_seconds())
            if best is None or gap < best:
                best, idx0 = gap, i

    systems = [_build_system(c, cells, times, idx0)
               for c in _merge(find_minima(cells, idx0))]
    systems.sort(key=lambda s: s["central_pressure_hpa"])

    result = {
        "available": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "valid_time_utc": times[idx0] if times else None,
        "active_systems_count": len(systems),
        "systems": systems,
        "message": ("No active low-pressure system detected in the North Indian Ocean."
                    if not systems else
                    f"{len(systems)} low-pressure system(s) detected from the live pressure field."),
        "scan": {
            "grid_points": len(points),
            "basins": [b["name"] for b in BASINS],
            "resolution_deg": BASINS[0]["step"],
            "lpa_threshold_hpa": LPA_THRESHOLD_HPA,
        },
        "data_source": "Open-Meteo mean-sea-level pressure and 10 m wind fields",
        "is_official_warning": False,
        "disclaimer": "WeatherGPT model estimate derived from a public forecast model. "
                      "Centre position is accurate to roughly +/-100 km and this is NOT an "
                      "official cyclone warning. IMD is the authoritative source.",
    }
    with _LOCK:
        _CACHE["systems"] = {"ts": now, "value": result}
    return result


# ------------------------------------------------------- per-location risk
def _distance_score(km: float) -> float:
    if km <= 100:  return 100.0
    if km >= 900:  return 0.0
    return round(100.0 * (900 - km) / 800.0, 1)


def cyclone_risk_for_location(name: str, lat: float, lon: float,
                              is_coastal: Optional[bool] = None,
                              local_gust_kmh: Optional[float] = None,
                              local_pressure_hpa: Optional[float] = None) -> Dict[str, Any]:
    """Cyclone risk for one place, from the detected systems plus local conditions."""
    scan = detect_active_systems()

    if not scan.get("available"):
        return {"location": name, "available": False, "risk_level": "UNKNOWN",
                "message": scan["message"], "is_official_warning": False}

    systems = scan["systems"]
    if not systems:
        return {
            "location": name, "available": True, "risk_score": 0.0,
            "risk_level": "NONE", "nearest_system": None,
            "message": "No active cyclone or low-pressure system detected in the "
                       "North Indian Ocean.",
            "checked_at": scan["timestamp"], "data_source": scan["data_source"],
            "is_official_warning": False,
        }

    ranked = sorted(
        ({"system": s,
          "distance_km": round(haversine_km(lat, lon, s["current_position"]["lat"],
                                            s["current_position"]["lon"]), 1)}
         for s in systems), key=lambda x: x["distance_km"])
    nearest = ranked[0]
    s = nearest["system"]
    dist = nearest["distance_km"]

    # Intensity MODULATES proximity rather than adding to it. Adding them let a
    # violent storm 1,600 km away score the same as a moderate one 900 km away,
    # which is wrong: cyclone risk at a location is driven by whether the system
    # can reach it at all. Beyond ~900 km proximity is zero, so the score is too.
    proximity = _distance_score(dist)
    intensity_factor = 0.45 + 0.55 * min(1.0, s["vmax_kmh"] / 180.0)
    score = proximity * intensity_factor

    notes = []
    if proximity <= 0:
        notes.append(f"Nearest system is {dist:.0f} km away - no direct cyclone "
                     f"impact expected at this location.")
    else:
        if is_coastal:
            score = min(100.0, score * 1.15)
            notes.append("Coastal location - exposed to storm surge and direct landfall winds.")
        if local_gust_kmh and local_gust_kmh >= 50:
            score = min(100.0, score + 6)
            notes.append(f"Local forecast gusts already {local_gust_kmh:.0f} km/h.")
        if local_pressure_hpa and local_pressure_hpa <= 1000:
            score = min(100.0, score + 5)
            notes.append(f"Local pressure {local_pressure_hpa:.0f} hPa is below normal.")

    score = round(score, 1)
    level = ("SEVERE" if score >= 75 else "HIGH" if score >= 50
             else "MODERATE" if score >= 25 else "LOW" if score > 0 else "NONE")

    return {
        "location": name, "available": True,
        "risk_score": score, "risk_level": level,
        "nearest_system": {
            "name": s["name"], "basin": s["basin"],
            "category": s["category"]["title"], "category_code": s["category"]["code"],
            "central_pressure_hpa": s["central_pressure_hpa"],
            "vmax_kmh": s["vmax_kmh"], "gust_kmh": s["gust_kmh"],
            "estimated_surge_m": s["estimated_surge_m"],
            "distance_km": dist,
            "bearing_from_location": bearing_to_compass(
                lat, lon, s["current_position"]["lat"], s["current_position"]["lon"]),
            "movement": s.get("movement"),
            "position_uncertainty_km": s["position_uncertainty_km"],
        },
        "other_systems": len(systems) - 1,
        "notes": notes,
        "checked_at": scan["timestamp"],
        "data_source": scan["data_source"],
        "is_official_warning": False,
        "disclaimer": scan["disclaimer"],
    }
