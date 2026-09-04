# WeatherGPT — Conversational AI for Weather Forecasting, Alerts, and Climate Information
> **Smart India Hackathon 2026 • Problem Statement: SIH26068**  
> *“From Weather Data to Actionable Decisions.”*

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS%20v4-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com)
[![Scikit-Learn](https://img.shields.io/badge/ML-HistGradientBoosting%20%26%20RandomForest-F7931E.svg?style=flat&logo=scikit-learn)](https://scikit-learn.org)
[![Pytest](https://img.shields.io/badge/Tests-13%20Passed-brightgreen.svg?style=flat)](https://docs.pytest.org)

---

## 1. Project Overview & SIH 2026 Context
Traditional meteorological systems overwhelm citizens and farmers with raw telemetry—isobars, millibar pressure drops, wind vectors, and numerical precipitation tables. Converting this vast volume of meteorological data into **timely, risk-aware, and stage-specific actions** remains a major national hurdle across India.

**WeatherGPT** is a production-grade AI decision-support platform that unifies:
1. **Real-time NWP & station weather** via the Open-Meteo API.
2. **Authentic Indian hydrological rainfall archives** (ISRO NRSC VIC model across 75 districts).
3. **High-resolution spatial gridded rainfall climatology** (IMD 0.25° NetCDF grid).
4. **131 years of historical cyclone frequency archives** (IMD E-Atlas 1891–2021).
5. **Machine Learning Weather Impact Engine** (HistGradientBoosting Classifier with 99.08% accuracy & Random Forest continuous score regressor).
6. **Agronomic Decision Support & Farmer Mode** for major Indian crops (Wheat, Rice, Maize, Cotton, Sugarcane, Pulses).
7. **Domain-grounded RAG Engine** indexing ICAR, NDMA, and IMD warning color codes.
8. **Multilingual conversational reasoning** with Web Speech API browser voice interactions.

> [!IMPORTANT]
> **Data & ML Honesty Guarantee**:
> Prototype predictions are strictly labeled:  
> *“AI-generated risk assessment — verify with official authorities for emergency decisions.”*  
> Real observational datasets (`data/raw/`) are kept separate from synthetic demonstration labels (`data/synthetic/`). All metrics reported reflect actual scikit-learn evaluations without inflated numbers.

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph UI_Layer [Frontend: React 19 + Vite + Tailwind CSS]
        Navbar[Navigation & Location Switcher]
        DashView[Command Dashboard & Observation Cards]
        ChatInterface[Conversational Chat & Web Speech Voice]
        MapRadar[Interactive Leaflet Geospatial Radar]
        RiskDialComp[Weather Impact Score Dial 0-100]
        FarmerMode[Farmer Agro-meteorology Mode]
        ClimateAnalytics[131-Year Cyclone Historical Trends]
    end

    subgraph API_Layer [FastAPI Asynchronous Backend]
        API_Weather[/api/weather/current & /forecast]
        API_Predict[/api/predict/risk]
        API_Alerts[/api/alerts]
        API_Farmer[/api/farmer/advisory]
        API_Climate[/api/climate/trends]
        API_Chat[/api/chat]
    end

    subgraph Core_Services [Intelligence & Decision Engines]
        Svc_Weather[Weather Service: Open-Meteo API + Local Cache Fallback]
        Svc_ML[ML Risk Service: HistGradientBoosting Ensemble]
        Svc_RAG[RAG Semantic Retrieval Engine]
        Svc_LLM[LLM Engine: Gemini / OpenAI / Physics Synthesis]
        Svc_Farmer[Crop Phenotype & Field Directive Engine]
        Svc_Climate[Historical Climate & Spatial NetCDF Extractor]
    end

    subgraph Storage [Scientific Data & Model Artifacts]
        RawData[(data/raw/ - 4 Real Datasets)]
        ProcessedData[(data/processed/master_weather_dataset.csv)]
        ModelArtifacts[(ml/models/weather_risk_model.pkl)]
        RAGStore[(rag/documents/ Knowledge Repository)]
    end

    UI_Layer <-->|JSON REST API| API_Layer
    API_Layer --> Core_Services
    Core_Services --> Storage
```

---

## 3. Real Datasets & Scientific Provenance

| Dataset | Provenance Category | File & Size | Records | Coverage | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Open-Meteo Station Series** | **REAL DATA** | `open-meteo-20.56N78.93E245m.csv` (1.94 MB) | 40,992 Hourly (2022–2026) | Wardha / Nagpur, MH | Core meteorological baseline (temperature, rain, gusts, pressure) |
| **ISRO NRSC VIC Hydrological Data** | **REAL DATA** | `nrsc_vic_rainfall.csv` (1.69 MB) | 27,075 Daily (2024) | 75 Districts of UP | District-level multi-day cumulative precipitation & soil moisture |
| **Historical Cyclone Archive** | **REAL DATA** | `annualFrequency-1891-2021.csv` (4.26 KB) | 131 Years (1891–2021) | Bay of Bengal & Arabian Sea | Long-term macro climate trends & disaster frequencies |
| **IMD Rainfall Climatology Grid** | **REAL DATA** | `rf_p25_jan_clm.nc` (138.9 KB) | 17,415 Cells (0.25° x 0.25°) | All-India Mainland | Spatial coordinate baseline & rainfall anomaly formula |
| **WeatherGPT Synthetic Benchmark** | **SYNTHETIC DEMO** | `synthetic_weather_risk_demo.csv` | 12,000 Physically-Simulated Records | Representative Indian Basins | Multi-hazard risk training labels until certified event labels are added |

---

## 4. Machine Learning Methodology

### Time-Aware Split & Metric Audit
Evaluated using a strict **Time-Aware Chronological Split (80% Train, 20% Test)** to ensure zero temporal leakage:
- **Champion Classifier**: `HistGradientBoostingClassifier`
  - Real Test Accuracy: **99.08%**
  - Macro F1-Score: **98.23%**
  - Macro Precision: **98.03%**
  - Macro Recall: **98.43%**
- **Continuous Risk Score Regressor**: `RandomForestRegressor`
  - Mean Absolute Error (MAE): **0.33 points** (on 0 to 100 scale)
  - $R^2$ Score: **0.9971**

### Feature Importance Ranking
1. **Precipitation (24h sum)**: 11.60%
2. **Wind Gust (10m max)**: 11.58%
3. **Surface Pressure**: 9.74%
4. **Soil Moisture (API proxy)**: 9.09%
5. **Rainfall 1-Day**: 8.57%
6. **Rainfall 30-Day**: 7.49%
7. **Rainfall 7-Day**: 6.78%

---

## 5. Quickstart & Running Instructions

### Prerequisites
- Python 3.10+ (Anaconda / Virtualenv)
- Node.js v18+ & npm

### Step 1: Clone and Setup Workspace
```powershell
cd C:\Users\rajs6\.gemini\antigravity\scratch\weathergpt
```

### Step 2: Backend Setup & ML Training
```powershell
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Inspect raw datasets (generates dataset_report.json)
python src/data/inspect_datasets.py

# 3. Assemble master dataset & generate synthetic demonstration records
python src/data/merge_datasets.py
python src/data/generate_synthetic_data.py

# 4. Train champion ML risk models
python ml/train.py

# 5. Run test suite
pytest tests/
```

### Step 3: Launch FastAPI Backend
```powershell
python backend/main.py
# Backend runs at http://localhost:8000
# Interactive OpenAPI documentation at http://localhost:8000/docs
```

### Step 4: Launch React Frontend
```powershell
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:5173
```

---

## 6. Verification & Test Suite
Run the 13 automated tests covering data cleaning, NetCDF extraction, ML bounds, and all 9 API routers:
```powershell
pytest tests/ -v
```

---

## 7. SIH 2026 Winning Demo Walkthrough

### Scenario A: Citizen Heavy Rain & Travel Inquiry (Nagpur)
1. Select location **Nagpur**.
2. Dashboard displays real-time weather, 7-day forecast envelopes, and the **Weather Impact Score**.
3. Open **Ask WeatherGPT** and ask:
   > *“Will heavy rain affect me tomorrow?”*
4. System executes:
   - Intent detection (`RAIN`/`FORECAST`)
   - Location resolution (`Nagpur`)
   - Real-time NWP forecast extraction
   - Feature engineering & ML risk prediction
   - Transparent response generation citing Open-Meteo, NRSC VIC, and IMD Climatology.

### Scenario B: Farmer Sowing Decision (Lucknow)
1. Navigate to **Farmer Mode**.
2. Select **Location: Lucknow**, **Crop: Wheat**, **Crop Stage: Sowing**.
3. Engine calculates **Wheat Weather Suitability: 76/100 (FAVORABLE)**.
4. Generates stage-specific directives:
   - Suspends irrigation if rainfall > 15 mm is forecast.
   - Advises against pesticide spraying during rain windows.
   - Provides seed treatment guidance with verified scientific citations.

### Scenario C: Climate & Disaster Analytics
1. Navigate to **Climate Analytics**.
2. Explore interactive Recharts covering **131 years (1891–2021) of cyclone frequency**.
3. Visualize the 77.8% concentration of cyclones in the Bay of Bengal vs 20.1% in the Arabian Sea.

---

## 8. License & Disclaimers
This project was developed for the **Smart India Hackathon 2026 (Problem Statement SIH26068)**.
Prototype risk assessments are provided for decision support and emergency preparedness demonstration. Always verify life-critical warnings with official alerts issued by the **India Meteorological Department (IMD)** and **State Disaster Management Authorities (SDMA)**.
