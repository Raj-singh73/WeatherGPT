"""
config.py - Application Configuration & Geocoding Index for WeatherGPT
SIH 2026 Problem Statement SIH26068
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ML_DIR = PROJECT_ROOT / "ml"
MODELS_DIR = ML_DIR / "models"
RAG_DIR = PROJECT_ROOT / "rag"

# Load .env if present
load_dotenv(PROJECT_ROOT / ".env")

class Settings:
    PROJECT_NAME: str = "WeatherGPT"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Conversational AI for Weather Forecasting, Alerts, and Climate Information (SIH 2026)"
    
    # LLM Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")
    
    # Live APIs
    OPEN_METEO_API_URL: str = os.getenv("WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast")
    OPEN_METEO_GEOCODING_URL: str = "https://geocoding-api.open-meteo.com/v1/search"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT}/weathergpt.db")
    
    # Paths
    DATA_DIR: Path = DATA_DIR
    PROCESSED_DATA_DIR: Path = PROCESSED_DATA_DIR
    RAW_DATA_DIR: Path = RAW_DATA_DIR
    MODEL_PATH: Path = MODELS_DIR / "weather_risk_model.pkl"
    METADATA_PATH: Path = MODELS_DIR / "model_metadata.json"
    NETCDF_PATH: Path = RAW_DATA_DIR / "rf_p25_jan_clm.nc"
    CYCLONE_CSV_PATH: Path = RAW_DATA_DIR / "annualFrequency-1891-2021.csv"
    NRSC_CSV_PATH: Path = RAW_DATA_DIR / "nrsc_vic_rainfall.csv"
    OPEN_METEO_CSV_PATH: Path = RAW_DATA_DIR / "open-meteo-20.56N78.93E245m.csv"
    
    # Built-in Geocoding Index for Offline / Rapid Indian Locations
    LOCATIONS: dict = {
        "nagpur": {"name": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lon": 79.0882, "climatology": 13.5},
        "wardha": {"name": "Wardha", "state": "Maharashtra", "lat": 20.7453, "lon": 78.6022, "climatology": 12.0},
        "lucknow": {"name": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lon": 80.9462, "climatology": 14.8},
        "delhi": {"name": "Delhi", "state": "Delhi", "lat": 28.6139, "lon": 77.2090, "climatology": 19.5},
        "new delhi": {"name": "New Delhi", "state": "Delhi", "lat": 28.6139, "lon": 77.2090, "climatology": 19.5},
        "mumbai": {"name": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lon": 72.8777, "climatology": 0.5},
        "varanasi": {"name": "Varanasi", "state": "Uttar Pradesh", "lat": 25.3176, "lon": 82.9739, "climatology": 15.2},
        "kanpur": {"name": "Kanpur", "state": "Uttar Pradesh", "lat": 26.4499, "lon": 80.3319, "climatology": 13.2},
        "kanpur nagar": {"name": "Kanpur Nagar", "state": "Uttar Pradesh", "lat": 26.4499, "lon": 80.3319, "climatology": 13.2},
        "kushi nagar": {"name": "Kushi Nagar", "state": "Uttar Pradesh", "lat": 26.9000, "lon": 83.8800, "climatology": 16.0},
        "kushinagar": {"name": "Kushi Nagar", "state": "Uttar Pradesh", "lat": 26.9000, "lon": 83.8800, "climatology": 16.0},
        "gorakhpur": {"name": "Gorakhpur", "state": "Uttar Pradesh", "lat": 26.7606, "lon": 83.3732, "climatology": 16.5},
        "agra": {"name": "Agra", "state": "Uttar Pradesh", "lat": 27.1767, "lon": 78.0081, "climatology": 8.35},
        "prayagraj": {"name": "Prayagraj", "state": "Uttar Pradesh", "lat": 25.4358, "lon": 81.8463, "climatology": 16.8},
        "meerut": {"name": "Meerut", "state": "Uttar Pradesh", "lat": 28.9845, "lon": 77.7064, "climatology": 21.0},
        "kolkata": {"name": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lon": 88.3639, "climatology": 14.0},
        "chennai": {"name": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707, "climatology": 24.5},
        "bengaluru": {"name": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lon": 77.5946, "climatology": 2.5},
        "hyderabad": {"name": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lon": 78.4867, "climatology": 6.8},
        "patna": {"name": "Patna", "state": "Bihar", "lat": 25.5941, "lon": 85.1376, "climatology": 14.2},
        "jaipur": {"name": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873, "climatology": 7.5},
        "bhopal": {"name": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lon": 77.4126, "climatology": 11.2},
        "bhubaneswar": {"name": "Bhubaneswar", "state": "Odisha", "lat": 20.2961, "lon": 85.8245, "climatology": 15.0},
        "puri": {"name": "Puri", "state": "Odisha", "lat": 19.8135, "lon": 85.8312, "climatology": 18.0},
        "ahmedabad": {"name": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lon": 72.5714, "climatology": 3.2}
    }

settings = Settings()
