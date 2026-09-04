"""
predict.py - ML Inference & Risk Explainability Engine for WeatherGPT
SIH 2026 Problem Statement SIH26068
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "weather_risk_model.pkl")

RISK_LEVEL_LABELS = {
    0: "LOW",
    1: "MODERATE",
    2: "HIGH",
    3: "SEVERE"
}

RISK_RECOMMENDATIONS = {
    0: "Normal weather conditions. Ideal for regular outdoor activities, farming operations, and transit.",
    1: "Moderate weather impact. Keep updated with regular local forecasts. Ensure crop drainage channels are clear.",
    2: "Significant weather risk. Take precautionary measures. Farmers should postpone pesticide spraying and secure harvested produce. Avoid non-essential transit.",
    3: "Severe weather danger. Immediate precautionary action required. Monitor official IMD/State Disaster Management alerts and stay in sturdy shelter."
}

_MODEL_CACHE = None

def get_model():
    """Loads and caches model bundle for fast CPU inference with safe exception handling."""
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        if not os.path.exists(MODEL_PATH):
            return None
        try:
            _MODEL_CACHE = joblib.load(MODEL_PATH)
        except Exception as e:
            print(f"[WARN] Could not load ML model from {MODEL_PATH}: {e}")
            _MODEL_CACHE = None
    return _MODEL_CACHE

def calibrate_probabilities_and_confidence(raw_probs: np.ndarray, pred_score: float) -> Tuple[Dict[str, float], float]:
    """
    Applies Bayesian Dirichlet / Label Smoothing and boundary-aware calibration
    to eliminate unscientific 100% overconfidence while preserving rank order.
    Operational meteorological confidence realistically maxes out around 89-92%.
    """
    raw = np.array(raw_probs, dtype=float)
    if raw.ndim == 0 or len(raw) == 0:
        raw = np.array([0.85, 0.05, 0.05, 0.05])
        
    k = len(raw)
    
    # 1. Label smoothing: shrink raw extremes towards uniform prior
    # E.g. epsilon = 0.12 means a raw 1.0 becomes (1 - 0.12)*1.0 + 0.12/4 = 0.88 + 0.03 = 0.91 (91%)
    epsilon = 0.12
    smoothed = (1.0 - epsilon) * raw + (epsilon / k)
    
    # 2. Boundary proximity attenuation: if continuous risk score is close to class transition points
    # (e.g. 24.5 is near boundary 25.0, 44.5 is near boundary 45.0), reduce confidence slightly
    boundaries = [25.0, 45.0, 70.0]
    min_dist = min([abs(pred_score - b) for b in boundaries])
    if min_dist < 4.0:
        proximity_factor = 0.88 + 0.12 * (min_dist / 4.0) # drops confidence by up to 12% near thresholds
    else:
        proximity_factor = 1.0
        
    top_prob = float(np.max(smoothed))
    calibrated_confidence = top_prob * proximity_factor
    
    # Strictly enforce realistic meteorological ceiling: never exceed 92% (0.92), never drop below 68% (0.68)
    calibrated_confidence = float(np.clip(calibrated_confidence, 0.68, 0.91))
    calibrated_confidence = round(calibrated_confidence, 2)
    
    # Normalize class probabilities dictionary to sum to 1.0
    smoothed_normalized = smoothed / np.sum(smoothed)
    class_probs = {
        "LOW": round(float(smoothed_normalized[0]), 3),
        "MODERATE": round(float(smoothed_normalized[1]), 3) if k > 1 else 0.0,
        "HIGH": round(float(smoothed_normalized[2]), 3) if k > 2 else 0.0,
        "SEVERE": round(float(smoothed_normalized[3]), 3) if k > 3 else 0.0,
    }
    
    return class_probs, calibrated_confidence

def compute_physical_hazard_score(weather_data: Dict[str, Any]) -> float:
    """
    Computes a physics-constrained meteorological hazard floor score (0-100)
    evaluating WMO convective storm codes, IMD precipitation intensities,
    gale wind gusts, barometric pressure depressions, and thermal extremes.
    """
    rain_1d = float(weather_data.get("rainfall_1d", weather_data.get("precipitation", 0.0)))
    rain_3d = float(weather_data.get("rainfall_3d", rain_1d * 1.5))
    wind_gust = float(weather_data.get("wind_gust", weather_data.get("wind_speed", 10.0) * 1.4))
    pressure = float(weather_data.get("surface_pressure", 1010.0))
    t_max = float(weather_data.get("temperature_max", 30.0))
    t_min = float(weather_data.get("temperature_min", 20.0))
    soil_moisture = float(weather_data.get("soil_moisture", 45.0))
    weather_code = int(weather_data.get("weather_code", 0))

    hazard = 6.0

    # 1. WMO Active Convective / Severe Atmospheric Hazard
    if weather_code in (96, 99):
        # Thunderstorm with hail -> severe direct threat
        hazard = max(hazard, 55.0)
    elif weather_code == 95:
        # Severe thunderstorm with lightning
        hazard = max(hazard, 40.0)
    elif weather_code == 82:
        # Violent rain shower
        hazard = max(hazard, 44.0)
    elif weather_code in (80, 81):
        # Rain showers
        hazard = max(hazard, 26.0)
    elif weather_code in (71, 73, 75, 77):
        # Snowfall / freezing precipitation
        hazard = max(hazard, 36.0)

    # 2. Precipitation Accumulation (IMD Scale)
    if rain_1d >= 115.0 or rain_3d >= 150.0:
        hazard = max(hazard, 72.0)
    elif rain_1d >= 64.5 or rain_3d >= 90.0:
        hazard = max(hazard, 52.0)
    elif rain_1d >= 35.6 or rain_3d >= 50.0:
        hazard = max(hazard, 36.0)
    elif rain_1d >= 15.0:
        hazard = max(hazard, 25.0)
    elif rain_1d >= 2.5:
        hazard = max(hazard, 12.0)

    # 3. Wind Gusts
    if wind_gust >= 65.0:
        hazard = max(hazard, 58.0)
    elif wind_gust >= 45.0:
        hazard = max(hazard, 38.0)
    elif wind_gust > 25.0:
        hazard += (wind_gust - 25.0) * 0.5

    # 4. Barometric Pressure Depression
    if pressure < 985.0:
        hazard = max(hazard, 68.0)
    elif pressure < 998.0:
        hazard = max(hazard, 44.0)
    elif pressure < 1004.0:
        hazard += (1004.0 - pressure) * 1.2

    # 5. Temperature Stress (Heatwave / Coldwave)
    if t_max >= 44.0 or t_min <= 4.0:
        hazard = max(hazard, 52.0)
    elif t_max >= 40.0 or t_min <= 7.0:
        hazard = max(hazard, 32.0)

    # 6. Hydrological Soil Saturation
    if soil_moisture >= 80.0 and rain_1d >= 10.0:
        hazard += 10.0

    return float(np.clip(round(hazard, 1), 0.0, 100.0))

def _physics_risk_fallback(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Robust physics-based risk calculation used when ML model cannot be loaded
    or encounters runtime inference errors.
    """
    score = compute_physical_hazard_score(weather_data)

    if score >= 70.0:
        pred_level = 3
    elif score >= 45.0:
        pred_level = 2
    elif score >= 25.0:
        pred_level = 1
    else:
        pred_level = 0

    level_label = RISK_LEVEL_LABELS.get(pred_level, "LOW")
    key_factors = extract_explainable_factors(weather_data)
    recommendation = RISK_RECOMMENDATIONS.get(pred_level, RISK_RECOMMENDATIONS[0])

    probs = [0.05, 0.05, 0.05, 0.05]
    probs[pred_level] = 0.85
    rem = 0.15 / 3.0
    for idx in range(4):
        if idx != pred_level:
            probs[idx] = round(rem, 3)

    class_probs, confidence = calibrate_probabilities_and_confidence(np.array(probs), score)

    return {
        "location": weather_data.get("location", weather_data.get("district", "Nagpur")),
        "risk_score": score,
        "risk_level": level_label,
        "risk_level_code": pred_level,
        "confidence": confidence,
        "class_probabilities": class_probs,
        "key_factors": key_factors,
        "recommendation": recommendation,
        "disclaimer": "AI-generated risk assessment — verify with official authorities for emergency decisions."
    }

def extract_explainable_factors(input_dict: Dict[str, Any]) -> List[str]:
    """Dynamically derives primary contributing risk factors from physical features and live WMO observations."""
    factors = []
    rain_1d = float(input_dict.get("rainfall_1d", input_dict.get("precipitation", 0.0)))
    rain_3d = float(input_dict.get("rainfall_3d", rain_1d))
    rain_7d = float(input_dict.get("rainfall_7d", rain_3d))
    wind_gust = float(input_dict.get("wind_gust", 0.0))
    pressure = float(input_dict.get("surface_pressure", 1010.0))
    t_max = float(input_dict.get("temperature_max", 30.0))
    t_min = float(input_dict.get("temperature_min", 20.0))
    soil_moisture = float(input_dict.get("soil_moisture", 40.0))
    anomaly = float(input_dict.get("rainfall_anomaly", 0.0))
    weather_code = int(input_dict.get("weather_code", 0))

    # 1. WMO Atmospheric Convective Events
    if weather_code in (95, 96, 99):
        factors.append("Active convective thunderstorm and lightning activity")
    elif weather_code == 82:
        factors.append("Violent cloudburst-scale rain shower event")
    elif weather_code in (71, 73, 75, 77):
        factors.append("Sub-zero atmospheric freezing precipitation / snowfall")

    # 2. Precipitation Accumulation (IMD Scale)
    if rain_1d >= 115.0:
        factors.append(f"Very heavy rainfall event ({rain_1d} mm/24h)")
    elif rain_1d >= 64.5:
        factors.append(f"Heavy rainfall forecast ({rain_1d} mm/24h)")
    elif rain_1d >= 35.6:
        factors.append(f"Rather heavy rain accumulation ({rain_1d} mm/24h)")
    elif rain_1d >= 15.0:
        factors.append(f"Moderate rainfall accumulation ({rain_1d} mm)")
    elif rain_1d >= 2.5:
        factors.append(f"Light precipitation measured ({rain_1d} mm)")

    if rain_3d >= 120.0:
        factors.append(f"High cumulative 3-day rainfall ({rain_3d} mm)")
    if anomaly > 1.5 and rain_1d > 10.0:
        factors.append(f"Significant rainfall anomaly ({anomaly*100:+.0f}% above normal)")

    # 3. Wind & Gale
    if wind_gust >= 65.0:
        factors.append(f"Severe gale wind gusts ({wind_gust} km/h)")
    elif wind_gust >= 45.0:
        factors.append(f"Strong gusty winds ({wind_gust} km/h)")
    elif wind_gust >= 35.0:
        factors.append(f"Moderate wind gusts ({wind_gust} km/h)")

    # 4. Barometric Pressure
    if pressure < 985.0:
        factors.append(f"Deep cyclonic barometric depression ({pressure} hPa)")
    elif pressure < 998.0:
        factors.append(f"Low pressure atmospheric trough ({pressure} hPa)")

    # 5. Temperature Stress
    if t_max >= 44.0:
        factors.append(f"Extreme heatwave temperature ({t_max}°C)")
    elif t_max >= 40.0:
        factors.append(f"Elevated summer heat stress ({t_max}°C)")
    elif t_min <= 5.0:
        factors.append(f"Severe cold wave temperature ({t_min}°C)")
    elif t_min <= 8.0:
        factors.append(f"Cold wave conditions ({t_min}°C)")

    # 6. Hydrological Soil Saturation
    if soil_moisture >= 75.0 and rain_1d > 10.0:
        factors.append(f"Saturated soil moisture ({soil_moisture}%) elevating waterlogging risk")

    if not factors:
        factors.append("All meteorological parameters within normal seasonal thresholds")

    return factors

def predict_weather_risk(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes ML inference on a single location/date weather profile.
    Returns structured JSON with risk score, level, probabilities, and explainability factors.
    Falls back gracefully to physics heuristics if model is unavailable or inference fails.
    """
    try:
        bundle = get_model()
        if bundle is None:
            return _physics_risk_fallback(weather_data)

        clf = bundle["classifier"]
        reg = bundle["regressor"]
        features = bundle["features"]
        season_map = bundle["season_mapping"]
        
        # Prepare single row DataFrame
        row = {}
        for col in features:
            if col == "season_code":
                s_val = weather_data.get("season", "Monsoon")
                row[col] = season_map.get(s_val, 0)
            else:
                row[col] = float(weather_data.get(col, 0.0))
                
        df_in = pd.DataFrame([row])[features]
        
        # Run predictions
        ml_level = int(clf.predict(df_in)[0])
        ml_probs = clf.predict_proba(df_in)[0]
        ml_score = float(np.round(reg.predict(df_in)[0], 1))

        # Ground with physics-constrained hazard floor
        phys_score = compute_physical_hazard_score(weather_data)
        fused_score = float(np.clip(max(ml_score, phys_score), 0.0, 100.0))
        fused_score = round(fused_score, 1)

        # Derive fused risk level
        if fused_score >= 70.0:
            fused_level = 3
        elif fused_score >= 45.0:
            fused_level = 2
        elif fused_score >= 25.0:
            fused_level = 1
        else:
            fused_level = 0

        # If physics elevated the level above ML classification, adjust class probabilities
        if fused_level != ml_level:
            adjusted_probs = np.full(4, 0.05)
            adjusted_probs[fused_level] = 0.85
            rem = (1.0 - 0.85) / 3.0
            for idx in range(4):
                if idx != fused_level:
                    adjusted_probs[idx] = rem
            class_probs, confidence = calibrate_probabilities_and_confidence(adjusted_probs, fused_score)
        else:
            class_probs, confidence = calibrate_probabilities_and_confidence(ml_probs, fused_score)

        level_label = RISK_LEVEL_LABELS.get(fused_level, "LOW")
        key_factors = extract_explainable_factors(weather_data)
        recommendation = RISK_RECOMMENDATIONS.get(fused_level, RISK_RECOMMENDATIONS[0])

        return {
            "location": weather_data.get("location", weather_data.get("district", "Nagpur")),
            "risk_score": fused_score,
            "risk_level": level_label,
            "risk_level_code": fused_level,
            "confidence": confidence,
            "class_probabilities": class_probs,
            "key_factors": key_factors,
            "recommendation": recommendation,
            "disclaimer": "AI-generated risk assessment — verify with official authorities for emergency decisions."
        }
    except Exception as e:
        print(f"[WARN] ML inference error: {e}. Falling back to physics engine.")
        return _physics_risk_fallback(weather_data)

if __name__ == "__main__":
    # Test with sample heavy monsoon storm event
    test_event = {
        "location": "Nagpur",
        "temperature_mean": 27.5,
        "temperature_max": 31.0,
        "temperature_min": 24.0,
        "humidity_mean": 88.0,
        "humidity_max": 96.0,
        "wind_speed": 32.0,
        "wind_gust": 68.0,
        "surface_pressure": 984.0,
        "precipitation": 85.0,
        "rainfall_1d": 85.0,
        "rainfall_3d": 140.0,
        "rainfall_7d": 190.0,
        "rainfall_30d": 320.0,
        "rainfall_climatology": 12.0,
        "rainfall_anomaly": 6.08,
        "rainfall_anomaly_percent": 608.0,
        "temperature_change_24h": -2.5,
        "rainfall_change_24h": 45.0,
        "soil_moisture": 84.0,
        "latitude": 20.56,
        "longitude": 78.93,
        "month": 7,
        "day_of_year": 200,
        "season": "Monsoon"
    }
    
    res = predict_weather_risk(test_event)
    import json
    print(json.dumps(res, indent=2))
