"""
climatology_service.py - Real per-location, per-date rainfall climatology for WeatherGPT
SIH 2026 Problem Statement SIH26068

WHY THIS EXISTS
---------------
Rainfall anomaly = (observed - climatological baseline) / baseline. The baseline
must match the observation in BOTH place and time of year, or the anomaly is
meaningless.

The repository previously had two baselines, neither of which satisfied that:

  1. data/raw/rf_p25_jan_clm.nc - a real IMD 0.25 deg gridded climatology, but it
     covers JANUARY ONLY. Using it in July compares monsoon rainfall against a
     winter baseline and reports enormous false anomalies.
  2. settings.LOCATIONS[...]["climatology"] - a hardcoded per-city constant, also
     a January figure, and only for 25 cities.

This module computes a genuine day-of-year climatology for any coordinate from
the free Open-Meteo Archive API (ERA5 reanalysis, no API key required): the mean
daily rainfall in a +/- window around the same calendar day, averaged over the
last N years.

HONESTY RULE
------------
If no trustworthy baseline can be obtained for a given place and date, this
module returns available=False. Callers must then SUPPRESS the anomaly rather
than substituting a wrong baseline. Never combine incompatible resolutions.
"""

import os
import json
import time
import math
import threading
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

import httpx

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

CLIMATOLOGY_YEARS = 10          # years of reanalysis to average over
WINDOW_DAYS = 7                 # +/- calendar-day window
GRID_DP = 1                     # cache/rounding resolution in decimal degrees (~11 km)
CACHE_TTL_SECONDS = 60 * 60 * 24 * 30   # a climatology does not change quickly
REQUEST_TIMEOUT = 20.0
MAX_RETRIES = 2

_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
_CACHE_FILE = _CACHE_DIR / "rainfall_climatology.json"
_MEM: Dict[str, Any] = {}
_LOCK = threading.Lock()
_LOADED = False

# Coordinates known to be outside the Open-Meteo land grid are not retried forever.
_NEGATIVE_TTL_SECONDS = 60 * 60 * 6


# ------------------------------------------------------------------ cache I/O
def _load_cache() -> None:
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    try:
        if _CACHE_FILE.exists():
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                _MEM.update(json.load(f))
    except Exception as e:
        print(f"[WARN] Climatology cache unreadable ({e}); starting empty.")


def _save_cache() -> None:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = _CACHE_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_MEM, f)
        tmp.replace(_CACHE_FILE)
    except Exception as e:
        print(f"[WARN] Could not persist climatology cache: {e}")


def _key(lat: float, lon: float) -> str:
    return f"{round(lat, GRID_DP)},{round(lon, GRID_DP)}"


# --------------------------------------------------------------- computation
def _fetch_daily_series(lat: float, lon: float, start: str, end: str) -> Optional[Dict[str, Any]]:
    """Fetches daily precipitation from the Open-Meteo Archive API, with retries."""
    params = {
        "latitude": round(lat, 4), "longitude": round(lon, 4),
        "start_date": start, "end_date": end,
        "daily": "precipitation_sum", "timezone": "Asia/Kolkata",
    }
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                resp = client.get(ARCHIVE_URL, params=params)
            if resp.status_code == 429:
                time.sleep(1.5 * (attempt + 1))       # rate limited - back off
                last_err = "rate_limited"
                continue
            if resp.status_code != 200:
                last_err = f"http_{resp.status_code}"
                break
            return resp.json().get("daily")
        except Exception as e:
            last_err = f"{type(e).__name__}"
            if attempt < MAX_RETRIES:
                time.sleep(0.8 * (attempt + 1))
    print(f"[WARN] Climatology archive fetch failed for {lat:.2f},{lon:.2f}: {last_err}")
    return None


def _build_climatology(lat: float, lon: float) -> Optional[Dict[str, float]]:
    """Builds a 366-entry day-of-year mean daily rainfall table for one location."""
    end = date.today() - timedelta(days=7)          # archive lags a few days
    start = date(end.year - CLIMATOLOGY_YEARS, 1, 1)
    daily = _fetch_daily_series(lat, lon, start.isoformat(), end.isoformat())
    if not daily:
        return None

    times, values = daily.get("time", []), daily.get("precipitation_sum", [])
    if len(times) < 365:
        return None

    buckets: Dict[int, list] = {}
    for t, v in zip(times, values):
        if v is None:
            continue
        try:
            doy = datetime.strptime(t, "%Y-%m-%d").timetuple().tm_yday
        except Exception:
            continue
        buckets.setdefault(doy, []).append(float(v))

    if len(buckets) < 300:
        return None

    table: Dict[str, float] = {}
    for doy in range(1, 367):
        window = []
        for offset in range(-WINDOW_DAYS, WINDOW_DAYS + 1):
            d = ((doy - 1 + offset) % 366) + 1
            window.extend(buckets.get(d, []))
        if window:
            table[str(doy)] = round(sum(window) / len(window), 3)
    return table or None


# ------------------------------------------------- local dataset fallback
# Tier 2 baseline. When the archive API is unreachable (or still warming), fall
# back to the project's OWN observed data rather than to a guess. This is real
# measured rainfall from data/processed/master_weather_dataset.csv - Open-Meteo
# station observations plus ISRO NRSC VIC district rainfall - reduced to a mean
# daily rainfall per location per calendar month.
_LOCAL_TABLE: Optional[list] = None
_LOCAL_TRIED = False


def _load_local_table() -> Optional[list]:
    """Builds [(lat, lon, {month: mean_mm}), ...] from the bundled dataset."""
    global _LOCAL_TABLE, _LOCAL_TRIED
    if _LOCAL_TRIED:
        return _LOCAL_TABLE
    _LOCAL_TRIED = True
    path = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "master_weather_dataset.csv"
    try:
        import pandas as pd
        if not path.exists():
            print(f"[INFO] Local climatology dataset not found at {path}")
            return None
        df = pd.read_csv(path, usecols=["latitude", "longitude", "month", "rainfall_1d"])
        grouped = (df.groupby(["latitude", "longitude", "month"])["rainfall_1d"]
                     .mean().reset_index())
        table: Dict[tuple, Dict[int, float]] = {}
        for _, r in grouped.iterrows():
            table.setdefault((float(r["latitude"]), float(r["longitude"])), {})[
                int(r["month"])] = round(float(r["rainfall_1d"]), 3)
        _LOCAL_TABLE = [(la, lo, months) for (la, lo), months in table.items()]
        print(f"[OK] Local rainfall climatology loaded: {len(_LOCAL_TABLE)} locations")
    except Exception as e:
        print(f"[WARN] Could not build local climatology fallback: {type(e).__name__}: {e}")
        _LOCAL_TABLE = None
    return _LOCAL_TABLE


def _local_climatology(lat: float, lon: float, month: int) -> Optional[float]:
    """Nearest-location monthly mean rainfall from the bundled dataset."""
    table = _load_local_table()
    if not table:
        return None
    best, best_d2 = None, None
    for la, lo, months in table:
        d2 = (la - lat) ** 2 + (lo - lon) ** 2
        if best_d2 is None or d2 < best_d2:
            best, best_d2 = months, d2
    if best is None or best_d2 is None:
        return None
    # Beyond roughly 3 degrees (~330 km) the baseline is not representative.
    if best_d2 > 9.0:
        return None
    return best.get(month)


# -------------------------------------------------------------- public entry
_WARMING: set = set()


def _warm_in_background(lat: float, lon: float) -> None:
    """Builds the climatology for a location off the request thread."""
    k = _key(lat, lon)
    with _LOCK:
        if k in _WARMING:
            return
        _WARMING.add(k)

    def _run():
        try:
            table = _build_climatology(lat, lon)
            with _LOCK:
                if table is None:
                    _MEM[k] = {"failed": True, "ts": time.time()}
                else:
                    _MEM[k] = {"table": table, "ts": time.time()}
                _save_cache()
        except Exception as e:
            print(f"[WARN] Background climatology build failed for {k}: {type(e).__name__}: {e}")
        finally:
            with _LOCK:
                _WARMING.discard(k)

    threading.Thread(target=_run, daemon=True, name=f"climatology-{k}").start()


def get_rainfall_climatology(lat: float, lon: float,
                             for_date: Optional[str] = None,
                             blocking: bool = False) -> Dict[str, Any]:
    """Returns the climatological mean daily rainfall (mm) for a place and date.

    Always returns a dict. Check `available` before using `value_mm`:

        {"available": True,  "value_mm": 9.4, "source": "Open-Meteo Archive (ERA5) ...",
         "day_of_year": 200, "window_days": 7, "years": 10}
        {"available": False, "value_mm": None, "source": None, "reason": "..."}
    """
    _load_cache()

    try:
        dt = datetime.strptime((for_date or "")[:10], "%Y-%m-%d").date() if for_date else date.today()
    except Exception:
        dt = date.today()
    doy = dt.timetuple().tm_yday

    k = _key(lat, lon)
    with _LOCK:
        entry = _MEM.get(k)
        now = time.time()

        if entry and entry.get("failed"):
            if now - entry.get("ts", 0) < _NEGATIVE_TTL_SECONDS:
                # The archive is unreachable for this location, but the project's
                # own observed dataset may still cover it. Try that before
                # giving up - a real local baseline beats no baseline.
                local = _local_climatology(lat, lon, dt.month)
                if local is not None:
                    return {"available": True, "value_mm": local,
                            "source": "Local historical dataset "
                                      "(data/processed/master_weather_dataset.csv, monthly mean)",
                            "day_of_year": doy, "tier": "local_dataset"}
                return {"available": False, "value_mm": None, "source": None,
                        "reason": "No verified climatology baseline for this location."}
            _MEM.pop(k, None)
            entry = None

        if entry and now - entry.get("ts", 0) < CACHE_TTL_SECONDS:
            table = entry.get("table", {})
            val = table.get(str(doy))
            if val is not None:
                return {"available": True, "value_mm": float(val),
                        "source": f"Open-Meteo Archive (ERA5), {CLIMATOLOGY_YEARS}-year mean, "
                                  f"+/-{WINDOW_DAYS} day window",
                        "day_of_year": doy, "window_days": WINDOW_DAYS,
                        "years": CLIMATOLOGY_YEARS, "cached": True}

    # Cold cache: building it fetches ~10 years of daily reanalysis, which can
    # take longer than the frontend's 10 s request timeout. Rather than block the
    # dashboard, warm the cache in the background and answer THIS request from
    # the local historical dataset instead.
    if not blocking:
        _warm_in_background(lat, lon)
        local = _local_climatology(lat, lon, dt.month)
        if local is not None:
            return {"available": True, "value_mm": local,
                    "source": "Local historical dataset "
                              "(data/processed/master_weather_dataset.csv, monthly mean)",
                    "day_of_year": doy, "tier": "local_dataset"}
        return {"available": False, "value_mm": None, "source": None,
                "reason": "Climatology baseline is being prepared for this location. "
                          "The rainfall anomaly will appear once it is ready."}

    table = _build_climatology(lat, lon)
    with _LOCK:
        if table is None:
            _MEM[k] = {"failed": True, "ts": time.time()}
            _save_cache()
            return {"available": False, "value_mm": None, "source": None,
                    "reason": "Climatology baseline could not be retrieved. "
                              "Rainfall anomaly is suppressed rather than estimated."}
        _MEM[k] = {"table": table, "ts": time.time()}
        _save_cache()

    val = table.get(str(doy))
    if val is None:
        return {"available": False, "value_mm": None, "source": None,
                "reason": "No baseline for this calendar day."}
    return {"available": True, "value_mm": float(val),
            "source": f"Open-Meteo Archive (ERA5), {CLIMATOLOGY_YEARS}-year mean, "
                      f"+/-{WINDOW_DAYS} day window",
            "day_of_year": doy, "window_days": WINDOW_DAYS,
            "years": CLIMATOLOGY_YEARS, "cached": False}


def compute_rainfall_anomaly(observed_mm: float, lat: float, lon: float,
                             for_date: Optional[str] = None,
                             blocking: bool = False) -> Dict[str, Any]:
    """Computes the rainfall anomaly, or reports honestly that it cannot.

    Returns keys the ML feature builder and the UI both consume:
        available, observed_mm, climatology_mm, anomaly_ratio,
        anomaly_percent, category, source, reason
    """
    clim = get_rainfall_climatology(lat, lon, for_date, blocking=blocking)
    if not clim.get("available"):
        return {"available": False, "observed_mm": round(float(observed_mm), 1),
                "climatology_mm": None, "anomaly_ratio": None, "anomaly_percent": None,
                "category": None, "source": None,
                "reason": clim.get("reason", "Baseline unavailable.")}

    baseline = float(clim["value_mm"])
    obs = float(observed_mm)

    # A near-zero baseline (dry season) makes the ratio explode. Report the
    # departure in millimetres instead of a meaningless percentage.
    if baseline < 0.2:
        return {"available": True, "observed_mm": round(obs, 1),
                "climatology_mm": round(baseline, 2), "anomaly_ratio": None,
                "anomaly_percent": None,
                "category": "Above a near-zero dry-season baseline" if obs > 0.2 else "Near normal (dry season)",
                "absolute_departure_mm": round(obs - baseline, 1),
                "source": clim["source"],
                "note": "Baseline is below 0.2 mm/day, so a percentage anomaly is not meaningful. "
                        "The departure is reported in mm."}

    ratio = (obs - baseline) / baseline
    pct = ratio * 100.0
    if pct >= 200:      cat = "Large excess"
    elif pct >= 60:     cat = "Excess"
    elif pct >= 20:     cat = "Above normal"
    elif pct > -20:     cat = "Near normal"
    elif pct > -60:     cat = "Below normal"
    else:               cat = "Deficient"

    return {"available": True, "observed_mm": round(obs, 1),
            "climatology_mm": round(baseline, 2),
            "anomaly_ratio": round(ratio, 3), "anomaly_percent": round(pct, 1),
            "absolute_departure_mm": round(obs - baseline, 1),
            "category": cat, "source": clim["source"],
            "tier": clim.get("tier", "archive_api"), "cached": clim.get("cached", False)}


if __name__ == "__main__":
    for name, la, lo in [("Lucknow", 26.8467, 80.9462), ("Nagpur", 21.1458, 79.0882)]:
        print(name, json.dumps(compute_rainfall_anomaly(25.0, la, lo, "2026-07-19"), indent=2))
