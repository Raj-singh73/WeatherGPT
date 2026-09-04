"""
test_backend.py - Integration Test Suite for WeatherGPT Backend Endpoints
SIH 2026 Problem Statement SIH26068
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app

client = TestClient(app)

def test_health():
    print("\n[TEST] 1. Testing GET /api/health ...")
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["ml_model_loaded"] is True
    print("  [OK] Health check passed:", data)

def test_current_weather():
    print("\n[TEST] 2. Testing GET /api/weather/current ...")
    res = client.get("/api/weather/current?location=Nagpur")
    assert res.status_code == 200
    data = res.json()
    assert data["location"] == "Nagpur"
    assert "temperature" in data["current"]
    assert "data_source" in data
    print(f"  [OK] Current weather for {data['location']}: {data['current']['temperature']}°C ({data['data_source']})")

def test_forecast():
    print("\n[TEST] 3. Testing GET /api/weather/forecast ...")
    res = client.get("/api/weather/forecast?location=Lucknow&days=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data["forecast_days"]) >= 5
    day1 = data["forecast_days"][0]
    assert "risk_score" in day1
    assert "risk_level" in day1
    print(f"  [OK] 5-day forecast for {data['location']} loaded. Day 1 Risk: {day1['risk_level']} (Score: {day1['risk_score']})")

def test_locations():
    print("\n[TEST] 4. Testing GET /api/weather/location ...")
    res = client.get("/api/weather/location")
    assert res.status_code == 200
    locs = res.json()
    assert len(locs) >= 15
    print(f"  [OK] Indexed locations loaded ({len(locs)} Indian stations)")

def test_risk_prediction():
    print("\n[TEST] 5. Testing POST /api/predict/risk ...")
    payload = {
        "location": "Nagpur",
        "temperature_mean": 29.0,
        "temperature_max": 34.0,
        "temperature_min": 25.0,
        "humidity_mean": 82.0,
        "humidity_max": 94.0,
        "wind_speed": 28.0,
        "wind_gust": 58.0,
        "surface_pressure": 988.0,
        "precipitation": 72.0,
        "rainfall_1d": 72.0,
        "rainfall_3d": 110.0,
        "rainfall_7d": 160.0,
        "rainfall_30d": 280.0,
        "rainfall_climatology": 13.5,
        "rainfall_anomaly": 4.33,
        "rainfall_anomaly_percent": 433.0,
        "temperature_change_24h": -1.5,
        "rainfall_change_24h": 35.0,
        "soil_moisture": 78.0,
        "month": 7,
        "day_of_year": 198,
        "season": "Monsoon"
    }
    res = client.post("/api/predict/risk", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ["LOW", "MODERATE", "HIGH", "SEVERE"]
    assert len(data["key_factors"]) > 0
    print(f"  [OK] Risk prediction passed: Score {data['risk_score']}, Level {data['risk_level']}")
    print(f"    Key factors: {data['key_factors'][:2]}")

def test_alerts():
    print("\n[TEST] 6. Testing GET /api/alerts ...")
    res = client.get("/api/alerts?location=Nagpur")
    assert res.status_code == 200
    data = res.json()
    assert data["total_active_alerts"] > 0
    assert data["alerts"][0]["is_demo"] is True
    print(f"  [OK] Multi-hazard alerts retrieved ({data['total_active_alerts']} active demo alerts)")

def test_climate_trends():
    print("\n[TEST] 7. Testing GET /api/climate/trends ...")
    res = client.get("/api/climate/trends")
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 131
    assert len(data["cyclone_trends"]) == 131
    print(f"  [OK] Historical climate records verified ({data['total_records']} years, 1891-2021)")

def test_farmer_advisory():
    print("\n[TEST] 8. Testing POST /api/farmer/advisory ...")
    payload = {
        "location": "Lucknow",
        "crop": "Wheat",
        "crop_stage": "Sowing"
    }
    res = client.post("/api/farmer/advisory", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert 0 <= data["suitability_score"] <= 100
    assert "irrigation_advice" in data
    assert "sowing_or_harvest_precaution" in data
    print(f"  [OK] Farmer advisory passed: {data['crop']} ({data['crop_stage']}) in {data['location']} -> {data['suitability_status']} ({data['suitability_score']}/100)")

def test_chat():
    print("\n[TEST] 9. Testing POST /api/chat ...")
    # Test query 1: Rain forecast query
    res = client.post("/api/chat", json={"message": "Will it rain tomorrow in Lucknow?", "language": "en"})
    assert res.status_code == 200
    d1 = res.json()
    assert d1["intent"] in ["RAIN", "FORECAST"]
    assert d1["extracted_location"] == "Lucknow"
    assert len(d1["sources"]) > 0
    print(f"  [OK] Chat query 1 passed: Intent={d1['intent']}, Loc={d1['extracted_location']}")
    
    # Test query 2: Hindi language query
    res_hi = client.post("/api/chat", json={"message": "kya kal Nagpur me baarish hogi?", "language": "hi"})
    assert res_hi.status_code == 200
    d2 = res_hi.json()
    assert d2["language"] == "hi"
    print("  [OK] Chat Hindi query passed successfully")

def test_exact_location_precision():
    print("\n[TEST] 10. Testing PIN & Village Geocoding Precision ...")
    # 1. Test 6-digit Indian PIN code lookup
    res_pin = client.get("/api/location/pincode?pincode=273303")
    assert res_pin.status_code == 200
    d_pin = res_pin.json()
    assert d_pin["status"] == "success"
    assert abs(d_pin["lat"] - 27.14) < 0.2
    assert abs(d_pin["lon"] - 83.51) < 0.2
    print(f"  [OK] PIN 273303 high-precision geocoded: {d_pin['lat']:.4f}°N, {d_pin['lon']:.4f}°E")

    # 2. Test Autocomplete suggestions precision
    res_sug = client.get("/api/location/suggest?q=Bhojpur")
    assert res_sug.status_code == 200
    s_list = res_sug.json()
    assert len(s_list) > 0
    assert "lat" in s_list[0] and "lon" in s_list[0]
    print(f"  [OK] Suggestion for Bhojpur returned {len(s_list)} items with GPS coordinates")

    # 3. Test Weather resolution with PIN
    res_w = client.get("/api/weather/current?location=273303")
    assert res_w.status_code == 200
    w_data = res_w.json()
    assert abs(w_data["latitude"] - 27.14) < 0.2
    assert abs(w_data["longitude"] - 83.51) < 0.2
    print(f"  [OK] Current weather resolved exact PIN coords: {w_data['latitude']:.4f}°N, {w_data['longitude']:.4f}°E")

if __name__ == "__main__":
    test_health()
    test_current_weather()
    test_forecast()
    test_locations()
    test_risk_prediction()
    test_alerts()
    test_climate_trends()
    test_farmer_advisory()
    test_chat()
    test_exact_location_precision()
    print("\n" + "="*50)
    print(" [ALL 10 BACKEND API SUITES PASSED CLEANLY]")
    print("="*50 + "\n")
