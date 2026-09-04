# WeatherGPT — REST API Reference
**SIH 2026 Problem Statement: SIH26068**

Base URL: `http://localhost:8000/api`

---

## 1. Health Endpoint
### `GET /api/health`
Verifies backend service, database, and ML model initialization.

**Sample Response**:
```json
{
  "status": "healthy",
  "app_name": "WeatherGPT",
  "version": "1.0.0",
  "ml_model_loaded": true,
  "live_weather_api": "https://api.open-meteo.com/v1/forecast",
  "provenance_mode": "Authentic Datasets (data/raw/) + Physics Demonstration ML"
}
```

---

## 2. Weather & Forecast
### `GET /api/weather/current`
Parameters:
- `location` (string, default: "Nagpur")

### `GET /api/weather/forecast`
Parameters:
- `location` (string, default: "Nagpur")
- `days` (int, default: 7)

### `GET /api/weather/location`
Lists pre-indexed Indian cities/districts with coordinates and January rainfall climatology.

---

## 3. ML Risk Prediction
### `POST /api/predict/risk`
**Request Body**:
```json
{
  "location": "Nagpur",
  "temperature_mean": 28.0,
  "temperature_max": 33.0,
  "temperature_min": 24.0,
  "humidity_mean": 75.0,
  "humidity_max": 90.0,
  "wind_speed": 20.0,
  "wind_gust": 45.0,
  "surface_pressure": 995.0,
  "precipitation": 45.0,
  "rainfall_1d": 45.0,
  "rainfall_3d": 75.0,
  "rainfall_7d": 110.0,
  "rainfall_30d": 210.0,
  "rainfall_climatology": 13.5,
  "rainfall_anomaly": 2.33,
  "rainfall_anomaly_percent": 233.0,
  "temperature_change_24h": -1.0,
  "rainfall_change_24h": 25.0,
  "soil_moisture": 68.0,
  "month": 7,
  "day_of_year": 195,
  "season": "Monsoon"
}
```

**Response**:
```json
{
  "location": "Nagpur",
  "risk_score": 64.5,
  "risk_level": "HIGH",
  "confidence": 0.96,
  "key_factors": [
    "Heavy rainfall forecast (45.0 mm/24h)",
    "Significant rainfall anomaly (+233% above normal)",
    "Strong gusty winds (45.0 km/h)"
  ],
  "recommendation": "Significant weather risk. Take precautionary measures. Farmers should postpone spraying.",
  "disclaimer": "AI-generated risk assessment — verify with official authorities for emergency decisions."
}
```

---

## 4. Multi-hazard Alerts
### `GET /api/alerts`
Parameters:
- `location` (string, default: "Nagpur")

---

## 5. Farmer Advisory
### `POST /api/farmer/advisory`
**Request Body**:
```json
{
  "location": "Lucknow",
  "crop": "Wheat",
  "crop_stage": "Sowing"
}
```

---

## 6. Conversational Chat
### `POST /api/chat`
**Request Body**:
```json
{
  "message": "Will it rain tomorrow in Lucknow?",
  "location": "Lucknow",
  "language": "en"
}
```
