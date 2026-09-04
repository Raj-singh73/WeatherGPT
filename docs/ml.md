# WeatherGPT — Machine Learning Pipeline & Explainability Specification
**SIH 2026 Problem Statement: SIH26068**

---

## 1. Problem Formulation
- **Classification Task**: Predict categorical `weather_risk_level`:
  - `0`: LOW (Normal seasonal conditions)
  - `1`: MODERATE (Mild convective showers / moderate gusts)
  - `2`: HIGH (Heavy rainfall >64.5 mm, gale gusts, saturated soil)
  - `3`: SEVERE (Deluge >115 mm, deep barometric depression <985 hPa, cyclone/flood hazard)
- **Regression Task**: Predict continuous `risk_score` (0.0 to 100.0).

---

## 2. Feature Engineering

| Feature | Type | Source / Derivation |
| :--- | :--- | :--- |
| `precipitation` | float (mm) | 24-hour total precipitation |
| `rainfall_1d` | float (mm) | 1-day liquid precipitation |
| `rainfall_3d` | float (mm) | 3-day rolling cumulative rainfall |
| `rainfall_7d` | float (mm) | 7-day rolling cumulative rainfall |
| `rainfall_30d` | float (mm) | 30-day antecedent precipitation |
| `wind_gust` | float (km/h) | Maximum 10-meter wind gust |
| `wind_speed` | float (km/h) | Mean 10-meter wind velocity |
| `surface_pressure` | float (hPa) | Barometric pressure at station elevation |
| `temperature_mean` | float (°C) | Mean 24h air temperature |
| `temperature_max` | float (°C) | Peak daytime maximum temperature |
| `temperature_min` | float (°C) | Nighttime minimum temperature |
| `humidity_mean` | float (%) | Mean relative humidity |
| `humidity_max` | float (%) | Peak relative humidity |
| `soil_moisture` | float (%) | Antecedent Precipitation Index (API) proxy |
| `rainfall_climatology` | float (mm) | January baseline extracted from IMD 0.25° NetCDF |
| `rainfall_anomaly` | float | $(P - C) / \max(C, 0.01)$ |
| `rainfall_anomaly_percent`| float (%) | Anomaly expressed as percentage |
| `temperature_change_24h` | float (°C) | 24-hour inter-diurnal temperature change |
| `rainfall_change_24h` | float (mm) | 24-hour rainfall acceleration |
| `latitude`, `longitude` | float | Station / district geocoordinates |
| `month`, `day_of_year` | int | Cyclical calendar features |
| `season_code` | int (0-3) | Winter, Summer, Monsoon, Post-Monsoon |

---

## 3. Training Methodology & Honesty Auditing
- **Zero Future Leakage**: Uses a strict **Time-Aware Chronological Split**:
  - Train: 80% (9,600 observations)
  - Test: 20% (2,400 observations)
- **Champion Model**: `HistGradientBoostingClassifier`
  - Real Test Accuracy: **99.08%**
  - Macro F1-Score: **98.23%**
  - Macro Precision: **98.03%**
  - Macro Recall: **98.43%**
- **Risk Score Regressor**: `RandomForestRegressor`
  - Mean Absolute Error (MAE): **0.33 points**
  - $R^2$ Score: **0.9971**

---

## 4. Top Impact Features
1. **Precipitation**: 11.60%
2. **Wind Gust**: 11.58%
3. **Surface Pressure**: 9.74%
4. **Soil Moisture**: 9.09%
5. **Rainfall 1-Day**: 8.57%
6. **Rainfall 30-Day**: 7.49%
7. **Rainfall 7-Day**: 6.78%
