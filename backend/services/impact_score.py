"""
impact_score.py - Multi-hazard Weather Impact Index for WeatherGPT
SIH 2026 Problem Statement SIH26068

WHY THIS MODULE EXISTS
----------------------
The previous Weather Impact Score came from a model trained on synthetic labels
that were a WEIGHTED AVERAGE of hazard sub-scores:

    score = 0.40*rain + 0.25*wind + 0.15*pressure + 0.10*temp + 0.10*soil

A weighted average caps every hazard at its own weight. Measured on the shipped
model, with all other inputs benign:

    gusts 120 km/h  -> 30.0  (0.25 * 100 + base)  -> classified LOW
    pressure 960 hPa -> 18.3  (0.15 * 100 + base) -> classified LOW
    temperature 48 C -> 21.8  (0.10 * 100 + base) -> classified LOW

A super-cyclone wind speed, a cyclone-core pressure and a lethal heatwave all
scored LOW. That is the accuracy failure.

WHAT THIS DOES INSTEAD
----------------------
Warnings do not average hazards - they escalate on the WORST one. This index
takes max() across hazard components, so any single severe hazard drives the
score, then adds a bounded compounding term when several hazards coincide.

It is a TRANSPARENT DETERMINISTIC INDEX, not a machine-learning prediction, and
it is labelled that way everywhere it surfaces. It is computed only from values
that are actually observed or forecast - never from values derived by multiplying
one another quantity.

THRESHOLDS
----------
Rain    : IMD 24-hour rainfall categories.
Wind    : IMD wind-warning / Beaufort damage bands.
Heat    : IMD heatwave criteria (plains).
Cold    : IMD cold-wave criteria.
Pressure: IMD low-pressure-system classification.
Every threshold is named in `component_detail` so the number can be audited.
"""

from typing import Dict, Any, Optional, List

LEVELS = {0: "LOW", 1: "MODERATE", 2: "HIGH", 3: "SEVERE"}

# Score bands -> categorical level.
BAND_MODERATE = 25.0
BAND_HIGH = 50.0
BAND_SEVERE = 75.0


def _piecewise(value: float, points: List[tuple]) -> float:
    """Linear interpolation across (threshold, score) breakpoints."""
    if value <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if value <= x1:
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (value - x0) / (x1 - x0)
    return points[-1][1]


# ----------------------------------------------------------------- hazards
def rain_component(mm_24h: Optional[float]) -> Optional[Dict[str, Any]]:
    """IMD 24-hour rainfall categories."""
    if mm_24h is None:
        return None
    v = max(0.0, float(mm_24h))
    s = _piecewise(v, [(0, 0), (2.5, 6), (15.6, 20), (35.5, 38),
                       (64.5, 58), (115.6, 78), (204.5, 95), (350.0, 100)])
    if v >= 204.5:   band = "Extremely heavy rain (IMD >204.4 mm)"
    elif v >= 115.6: band = "Very heavy rain (IMD 115.6-204.4 mm)"
    elif v >= 64.5:  band = "Heavy rain (IMD 64.5-115.5 mm)"
    elif v >= 35.5:  band = "Rather heavy rain (IMD 35.6-64.4 mm)"
    elif v >= 15.6:  band = "Moderate rain (IMD 15.6-35.5 mm)"
    elif v >= 2.5:   band = "Light rain (IMD 2.5-15.5 mm)"
    else:            band = "No or very light rain"
    return {"hazard": "Rainfall", "score": round(s, 1),
            "value": round(v, 1), "unit": "mm/24h", "band": band}


def wind_component(gust_kmh: Optional[float]) -> Optional[Dict[str, Any]]:
    """IMD wind-warning / Beaufort damage bands."""
    if gust_kmh is None:
        return None
    v = max(0.0, float(gust_kmh))
    s = _piecewise(v, [(0, 0), (20, 5), (40, 18), (50, 32),
                       (62, 50), (88, 72), (118, 90), (170, 100)])
    if v >= 118:  band = "Hurricane-force gusts (>=118 km/h)"
    elif v >= 88: band = "Storm-force gusts (88-117 km/h)"
    elif v >= 62: band = "Gale-force gusts (62-87 km/h)"
    elif v >= 50: band = "Strong squally winds (50-61 km/h)"
    elif v >= 40: band = "Squally winds (40-49 km/h)"
    else:         band = "Light to moderate winds"
    return {"hazard": "Wind", "score": round(s, 1),
            "value": round(v, 1), "unit": "km/h gust", "band": band}


def heat_component(t_max: Optional[float], normal_t_max: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """IMD heatwave criteria for the plains, plus departure-from-normal when known."""
    if t_max is None:
        return None
    v = float(t_max)
    # IMD plains heatwave threshold is max >= 40 C. 36-39 C is ordinary
    # pre-monsoon heat across central India and should stay low.
    s = _piecewise(v, [(32, 0), (38, 8), (40, 30), (42, 50), (45, 75), (47.5, 90), (52, 100)])
    band = ("Extreme heat (>=45 C)" if v >= 45 else
            "Severe heatwave range (42-44.9 C)" if v >= 42 else
            "Heatwave range (40-41.9 C)" if v >= 40 else
            "Warm (36-39.9 C)" if v >= 36 else "Normal temperatures")
    detail = {"hazard": "Heat", "score": round(s, 1),
              "value": round(v, 1), "unit": "C max", "band": band}
    if normal_t_max is not None:
        dep = v - float(normal_t_max)
        detail["departure_from_normal_c"] = round(dep, 1)
        # IMD: heatwave when departure >= 4.5 C, severe when >= 6.5 C.
        if dep >= 6.5:
            detail["score"] = round(max(detail["score"], 75.0), 1)
            detail["band"] = f"Severe heatwave departure (+{dep:.1f} C vs normal)"
        elif dep >= 4.5:
            detail["score"] = round(max(detail["score"], 50.0), 1)
            detail["band"] = f"Heatwave departure (+{dep:.1f} C vs normal)"
    return detail


def cold_component(t_min: Optional[float]) -> Optional[Dict[str, Any]]:
    """IMD cold-wave criteria for the plains."""
    if t_min is None:
        return None
    v = float(t_min)
    # IMD plains cold wave is min <= 4 C. A 8-10 C winter night across north
    # India is normal and must not register as a hazard.
    s = _piecewise(-v, [(-12, 0), (-10, 3), (-8, 8), (-6, 20),
                        (-4, 45), (-2, 65), (0, 82), (3, 100)])
    band = ("Severe cold wave (<=-2 C)" if v <= -2 else
            "Cold wave (<=4 C)" if v <= 4 else
            "Cold (<=6 C)" if v <= 6 else
            "Cool (<=10 C)" if v <= 10 else "Normal night temperatures")
    return {"hazard": "Cold", "score": round(s, 1),
            "value": round(v, 1), "unit": "C min", "band": band}


def pressure_component(hpa: Optional[float]) -> Optional[Dict[str, Any]]:
    """IMD low-pressure-system classification by central pressure."""
    if hpa is None:
        return None
    v = float(hpa)
    # Calibrated for India: monsoon-season surface pressure routinely sits
    # 1000-1008 hPa, so those values must contribute ~nothing. Escalation
    # begins at the IMD depression threshold and below.
    s = _piecewise(-v, [(-1012, 0), (-1004, 2), (-1000, 8), (-996, 20),
                        (-992, 38), (-986, 60), (-978, 82), (-968, 100)])
    band = ("Intense cyclonic core (<=975 hPa)" if v <= 975 else
            "Deep depression / cyclone (<=985 hPa)" if v <= 985 else
            "Depression (<=992 hPa)" if v <= 992 else
            "Low pressure area (<=998 hPa)" if v <= 998 else
            "Slightly below normal" if v <= 1004 else "Normal pressure")
    return {"hazard": "Pressure", "score": round(s, 1),
            "value": round(v, 1), "unit": "hPa", "band": band}


def saturation_component(rain_7d: Optional[float], rain_1d: Optional[float]) -> Optional[Dict[str, Any]]:
    """Antecedent wetness: saturated ground turns moderate rain into flooding."""
    if rain_7d is None:
        return None
    v = max(0.0, float(rain_7d))
    s = _piecewise(v, [(0, 0), (40, 8), (80, 22), (150, 45), (250, 68), (400, 85)])
    # Only meaningful while it is actually raining.
    if (rain_1d or 0.0) < 10.0:
        s *= 0.4
    band = ("Saturated ground (>=150 mm in 7 days)" if v >= 150 else
            "Wet ground (80-149 mm in 7 days)" if v >= 80 else
            "Damp ground (40-79 mm in 7 days)" if v >= 40 else "Dry ground")
    return {"hazard": "Ground saturation", "score": round(s, 1),
            "value": round(v, 1), "unit": "mm/7d", "band": band}


# ------------------------------------------------------------------ index
def compute_impact_score(
    precipitation_mm: Optional[float] = None,
    wind_gust_kmh: Optional[float] = None,
    temperature_max_c: Optional[float] = None,
    temperature_min_c: Optional[float] = None,
    surface_pressure_hpa: Optional[float] = None,
    rainfall_7d_mm: Optional[float] = None,
    rainfall_anomaly_ratio: Optional[float] = None,
    normal_temperature_max_c: Optional[float] = None,
) -> Dict[str, Any]:
    """Computes the Weather Impact Index (0-100) from OBSERVED/FORECAST values.

    Any argument left as None is treated as unavailable and simply does not
    contribute - it is never replaced by a derived or default value.
    """
    components = [c for c in (
        rain_component(precipitation_mm),
        wind_component(wind_gust_kmh),
        heat_component(temperature_max_c, normal_temperature_max_c),
        cold_component(temperature_min_c),
        pressure_component(surface_pressure_hpa),
        saturation_component(rainfall_7d_mm, precipitation_mm),
    ) if c is not None]

    if not components:
        return {"available": False, "score": None, "level": None,
                "reason": "No weather values were available to compute an impact score."}

    components.sort(key=lambda c: -c["score"])
    dominant = components[0]
    base = dominant["score"]

    # Compounding: additional hazards raise the score but can never let two mild
    # hazards outrank one severe hazard. Capped at +15.
    others = [c["score"] for c in components[1:]]
    compounding = min(15.0, sum(s * 0.18 for s in others))

    # Anomaly amplifier: rain far above the local seasonal normal is more
    # disruptive than the same rain in its normal season. Applied only when a
    # real climatology baseline was supplied.
    anomaly_bonus = 0.0
    anomaly_note = None
    if rainfall_anomaly_ratio is not None and (precipitation_mm or 0.0) >= 10.0:
        r = float(rainfall_anomaly_ratio)
        if r >= 1.0:
            anomaly_bonus = min(10.0, 4.0 * min(r, 3.0))
            anomaly_note = f"Rainfall is {r * 100:.0f}% above the local seasonal normal"

    score = min(100.0, base + compounding + anomaly_bonus)

    level = (3 if score >= BAND_SEVERE else
             2 if score >= BAND_HIGH else
             1 if score >= BAND_MODERATE else 0)

    return {
        "available": True,
        "score": round(score, 1),
        "level": LEVELS[level],
        "level_code": level,
        "dominant_hazard": dominant["hazard"],
        "dominant_band": dominant["band"],
        "components": components,
        "compounding_bonus": round(compounding, 1),
        "anomaly_bonus": round(anomaly_bonus, 1),
        "anomaly_note": anomaly_note,
        "method": "WeatherGPT Multi-hazard Impact Index (max-of-hazards, IMD thresholds)",
        "is_machine_learning": False,
        "is_official_warning": False,
        "disclaimer": "Deterministic index computed from observed and forecast values. "
                      "Not an official IMD warning.",
    }


def explain_impact(result: Dict[str, Any], limit: int = 4) -> List[str]:
    """Human-readable drivers, ordered by actual contribution."""
    if not result.get("available"):
        return ["Verified information is currently unavailable."]
    out = [f"{c['hazard']}: {c['value']} {c['unit']} — {c['band']}"
           for c in result["components"][:limit] if c["score"] > 0]
    if not out:
        out.append("All measured parameters are within normal seasonal ranges.")
    if result.get("anomaly_note"):
        out.append(result["anomaly_note"])
    out.append(f"Highest-impact factor: {result['dominant_hazard']} "
               f"(index {result['score']}/100, {result['level']})")
    return out
