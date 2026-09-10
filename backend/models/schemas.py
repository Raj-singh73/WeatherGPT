"""
schemas.py - Pydantic Request & Response Data Contracts for WeatherGPT API
SIH 2026 Problem Statement SIH26068
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class HealthResponse(BaseModel):
    status: str = "healthy"
    app_name: str = "WeatherGPT"
    version: str = "1.0.0"
    ml_model_loaded: bool
    live_weather_api: str
    provenance_mode: str = "Real datasets + Physics-constrained ML"

class LocationItem(BaseModel):
    name: str
    state: str
    latitude: float
    longitude: float
    rainfall_climatology_mm: float

class CurrentWeatherMetrics(BaseModel):
    temperature: float
    apparent_temperature: float
    relative_humidity: float
    precipitation: float
    rain: float
    wind_speed: float
    wind_gust: float
    surface_pressure: float
    weather_code: int
    weather_description: str
    is_day: int
    timestamp: str
    precipitation_probability: Optional[float] = 0.0
    precipitation_intensity: Optional[str] = "No Rain"

class WeatherCurrentResponse(BaseModel):
    location: str
    state: str
    latitude: float
    longitude: float
    elevation_m: float
    data_source: str # "LIVE (Open-Meteo API)" or "DEMO/OFFLINE (Historical Observation)"
    current: CurrentWeatherMetrics

class DailyForecastItem(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    precipitation_sum: float
    rain_sum: float
    wind_speed_max: float
    wind_gust_max: float
    weather_code: int
    weather_description: str
    risk_score: float
    risk_level: str
    confidence: Optional[float] = None
    key_factors: Optional[List[str]] = []
    recommendation: Optional[str] = ""
    precipitation_probability_max: Optional[float] = 0.0
    precipitation_hours: Optional[float] = 0.0
    precipitation_category: Optional[str] = "No Rain"
    # --- additive: impact-index provenance ---
    method: Optional[str] = None
    is_machine_learning: Optional[bool] = None
    dominant_hazard: Optional[str] = None
    dominant_band: Optional[str] = None
    hazard_components: Optional[List[Dict[str, Any]]] = None
    inputs_available: Optional[str] = None
    rainfall_anomaly: Optional[Dict[str, Any]] = None
    antecedent_quality: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None

class WeatherForecastResponse(BaseModel):
    location: str
    state: str
    latitude: float
    longitude: float
    data_source: str
    forecast_days: List[DailyForecastItem]

class RiskPredictionRequest(BaseModel):
    location: Optional[str] = "Nagpur"
    latitude: Optional[float] = 21.1458
    longitude: Optional[float] = 79.0882
    temperature_mean: Optional[float] = None
    temperature_max: Optional[float] = 30.0
    temperature_min: Optional[float] = 22.0
    humidity_mean: Optional[float] = 70.0
    humidity_max: Optional[float] = 85.0
    wind_speed: Optional[float] = 15.0
    wind_gust: Optional[float] = None
    surface_pressure: Optional[float] = 1010.0
    precipitation: float = 0.0
    rainfall_1d: Optional[float] = None
    rainfall_3d: Optional[float] = None
    rainfall_7d: Optional[float] = None
    rainfall_30d: Optional[float] = None
    rainfall_climatology: Optional[float] = 12.0
    rainfall_anomaly: Optional[float] = None
    rainfall_anomaly_percent: Optional[float] = None
    temperature_change_24h: Optional[float] = 0.0
    rainfall_change_24h: Optional[float] = None
    soil_moisture: Optional[float] = None
    month: Optional[int] = None
    day_of_year: Optional[int] = None
    season: Optional[str] = None

class RiskPredictionResponse(BaseModel):
    location: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: str
    risk_level_code: int
    confidence: Optional[float] = None
    class_probabilities: Dict[str, float] = {}
    key_factors: List[str]
    recommendation: str
    disclaimer: str = (
        "WeatherGPT Weather Impact Index — a deterministic index computed from observed "
        "and forecast values, not an official forecast or warning. IMD remains the "
        "authoritative source; verify before any emergency decision."
    )
    # --- additive: impact-index provenance (all optional; nothing removed) ---
    method: Optional[str] = None
    is_machine_learning: Optional[bool] = None
    dominant_hazard: Optional[str] = None
    dominant_band: Optional[str] = None
    hazard_components: Optional[List[Dict[str, Any]]] = None
    inputs_available: Optional[str] = None
    season: Optional[str] = None
    rainfall_anomaly: Optional[Dict[str, Any]] = None
    antecedent_quality: Optional[str] = None
    antecedent_source: Optional[str] = None
    estimate_available: Optional[bool] = True
    provenance: Optional[Dict[str, Any]] = None

class AlertItem(BaseModel):
    id: str
    title: str
    location: str
    state: str
    severity: str # "NORMAL", "WATCH", "WARNING", "SEVERE"
    alert_type: str # "HEAVY_RAIN", "THUNDERSTORM", "HEATWAVE", "CYCLONE_ALERT", "FLOOD_RISK"
    issued_time: str
    valid_until: str
    source: str # "DEMO ALERT (AI Simulated Multi-hazard Threshold)"
    is_demo: bool = True
    summary: str
    action_instructions: str
    vulnerability_zone: Optional[str] = "Inland Alluvial Plains"
    hazard_category: Optional[str] = "HYDRO_METEOROLOGICAL"
    imd_color_code: Optional[str] = "YELLOW" # RED, ORANGE, YELLOW, GREEN
    life_survival_protocols: Optional[List[str]] = []
    emergency_contacts: Optional[Dict[str, str]] = {}
    key_thresholds: Optional[List[str]] = []

class AlertsResponse(BaseModel):
    total_active_alerts: int
    alerts: List[AlertItem]
    disclaimer: str = "DEMO ALERT — AI-generated multi-hazard advisory for prototype testing."

class CycloneRecordItem(BaseModel):
    year: int
    cyclonic_disturbances_total: int
    cyclones_total: int
    severe_cyclones_total: int
    cyclones_bob: int
    cyclones_as: int

class ClimateTrendsResponse(BaseModel):
    description: str
    data_source: str = "IMD Cyclone E-Atlas (1891-2021)"
    total_records: int
    period: str
    cyclone_trends: List[CycloneRecordItem]
    climatology_baseline: Dict[str, Any]

class FarmerAdvisoryRequest(BaseModel):
    location: str = "Lucknow"
    crop: str = "Wheat" # Wheat, Rice, Maize, Cotton, Sugarcane, Pulses
    crop_stage: str = "Sowing" # Sowing, Vegetative, Flowering, Maturity, Harvesting
    soil_type: Optional[str] = "Alluvial / Loam"
    language: Optional[str] = "en"

class FarmerAdvisoryResponse(BaseModel):
    crop: str
    crop_stage: str
    location: str
    suitability_score: float = Field(..., ge=0.0, le=100.0)
    suitability_status: str # "OPTIMAL", "FAVORABLE", "CAUTION", "UNFAVORABLE"
    weather_concern: str
    irrigation_advice: str
    sowing_or_harvest_precaution: str
    heat_or_rain_stress_warning: str
    recommendation: str
    why_factors: List[str]
    data_sources: List[str]
    disclaimer: str = "AI-generated agricultural advisory — consult local Krishi Vigyan Kendra (KVK) for authoritative guidance."
    current_season: Optional[str] = None
    is_in_season: Optional[bool] = True
    seasonal_crops_recommended: Optional[List[str]] = []
    season_warning: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    location: Optional[str] = "Nagpur"
    language: Optional[str] = "en" # en, hi, mr, bn, ta, te, gu
    persona: Optional[str] = "GENERAL" # FARMER, COMMUTER, EVENT_OUTDOOR, HEALTH_DAILY, GENERAL
    crop: Optional[str] = None
    crop_stage: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    extracted_location: str
    language: str
    persona: Optional[str] = "GENERAL"
    risk_assessment: Optional[Dict[str, Any]] = None
    sources: List[str]
    confidence: float = 0.95
    verdict: Optional[str] = None # "RECOMMENDED", "CAUTION", "NOT_RECOMMENDED", "INFO"
    verdict_badge: Optional[str] = None # e.g. "🟢 RECOMMENDED", "🟡 CAUTION", "🔴 NOT RECOMMENDED"
    use_case: Optional[str] = None # e.g. "LAUNDRY_DRYING", "CAR_WASH", "OUTDOOR_SPORTS", etc.
    suitability_score: Optional[float] = None # 0 to 100
    action_steps: Optional[List[str]] = None
    weather_summary: Optional[Dict[str, Any]] = None
    transcribed_text: Optional[str] = None
    detected_language: Optional[str] = None
    speech_text: Optional[str] = None
    audio_url: Optional[str] = None


# =====================================================================
# Authentication & User Profile Schemas
# =====================================================================

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)
    role: Optional[str] = "Farmer"  # Farmer, Citizen, Agricultural Scientist, Disaster Manager, Researcher
    phone: Optional[str] = None
    state: Optional[str] = "Uttar Pradesh"
    district: Optional[str] = "Lucknow"
    village: Optional[str] = None
    primary_crop: Optional[str] = "Wheat"
    preferred_language: Optional[str] = "en"

class UserLoginRequest(BaseModel):
    email: str
    password: str

class PasswordResetRequest(BaseModel):
    email: str
    new_password: str = Field(..., min_length=6, max_length=128)

class UserProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    primary_crop: Optional[str] = None
    preferred_language: Optional[str] = "en"
    created_at: str
    last_login_at: Optional[str] = None
    updated_at: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    primary_crop: Optional[str] = None
    preferred_language: Optional[str] = None

class AuthTokenResponse(BaseModel):
    token: str
    token_type: str = "Bearer"
    user: UserProfileResponse
    message: Optional[str] = "Authentication successful"

class AdminRecordsResponse(BaseModel):
    total_users: int
    users: List[Dict[str, Any]]
    recent_logs: List[Dict[str, Any]]


