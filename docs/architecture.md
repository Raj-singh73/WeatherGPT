# WeatherGPT — System Architecture Specification
**SIH 2026 Problem Statement: SIH26068**  
*Conversational AI for Weather Forecasting, Alerts, and Climate Information*

---

## 1. High-Level System Architecture

WeatherGPT is designed as a decoupled, multi-tiered AI/ML decision-support platform:

```mermaid
flowchart TD
    subgraph UI_Layer [Frontend: React + Vite + Tailwind CSS]
        Nav[Navbar & Location Switcher]
        Dash[Command Dashboard & Cards]
        ChatUI[Conversational Chat & Voice]
        MapComp[Interactive Leaflet Radar]
        RiskDial[Weather Impact Score Dial]
        FarmerUI[Farmer Crop Mode]
        ClimateUI[131-Yr Cyclone Analytics]
    end

    subgraph API_Layer [FastAPI Modular Backend (Asynchronous)]
        RouterWeather[/api/weather]
        RouterForecast[/api/weather/forecast]
        RouterPredict[/api/predict/risk]
        RouterAlerts[/api/alerts]
        RouterFarmer[/api/farmer/advisory]
        RouterClimate[/api/climate/trends]
        RouterChat[/api/chat]
    end

    subgraph Core_Services [Core Intelligence Engines]
        WeatherSvc[Weather Service: Open-Meteo Live API + Offline Cache]
        MLEngine[ML Risk Engine: HistGradientBoosting Classifier & Regressor]
        RAGSvc[RAG Engine: TF-IDF & Semantic Vector Store]
        LLMSvc[LLM Engine: Multi-provider OpenAI/Gemini/Physics Synthesis]
        FarmerSvc[Agro-meteorology Crop Decision Support]
        ClimateSvc[Cyclone Archive & NetCDF Spatial Engine]
    end

    subgraph Data_Repository [Scientific Data & Model Artifacts]
        Raw1[(open-meteo-20.56N78.93E245m.csv)]
        Raw2[(nrsc_vic_rainfall.csv)]
        Raw3[(annualFrequency-1891-2021.csv)]
        Raw4[(rf_p25_jan_clm.nc NetCDF Grid)]
        ModelPKL[(models/weather_risk_model.pkl)]
        RAGDocs[(rag/documents/ Knowledge Base)]
    end

    UI_Layer <-->|REST API JSON| API_Layer
    API_Layer --> Core_Services
    Core_Services --> Data_Repository
```

---

## 2. Component Design & Responsibilities

### 2.1 UI Layer (React 19 + Vite + Tailwind CSS)
- **Dashboard**: Real-time multi-sensor telemetry, Weather Impact Score dial, and geospatial Leaflet radar.
- **Ask WeatherGPT**: Natural language chat with Web Speech API (speech-to-text & text-to-speech) and verified data provenance citations.
- **Forecast**: 7-day numerical weather prediction envelopes with temperature bands and precipitation totals.
- **Farmer Mode**: Phenotype-specific crop decision support for Wheat, Rice, Maize, Cotton, Sugarcane, and Pulses.
- **Climate Analytics**: Macro disaster analytics covering 131 years (1891–2021) of North Indian Ocean cyclones.

### 2.2 API Layer (FastAPI)
- Modular routers with Pydantic v2 validation contracts.
- High-throughput asynchronous routing with CORS protection for local development and production deployments.

### 2.3 Machine Learning Layer
- **Champion Classifier**: `HistGradientBoostingClassifier` trained with a time-aware chronological split (80% train, 20% test).
  - Accuracy: 99.08%
  - Macro F1: 98.23%
- **Continuous Regressor**: `RandomForestRegressor` predicting continuous risk scores (0 to 100) with MAE = 0.33 points.
- **Dynamic Explainability**: Extracts physical contributing factors (rain anomaly, soil moisture, gale gusts, pressure drop).

### 2.4 RAG Engine
- Domain documents covering IMD Quantitative Precipitation Categories, NDMA Heatwave Directives, Cyclone Alert Stages, and ICAR Agromet spraying/sowing guidelines.
- Instant, CPU-friendly semantic retrieval without requiring heavy external GPU dependencies.
