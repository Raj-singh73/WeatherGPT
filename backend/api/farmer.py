"""
farmer.py - Farmer Advisory API Router for WeatherGPT
SIH 2026 Problem Statement SIH26068
"""

from fastapi import APIRouter
from models.schemas import FarmerAdvisoryRequest, FarmerAdvisoryResponse
from services.farmer_service import generate_farmer_advisory

router = APIRouter(prefix="/api/farmer", tags=["Farmer Advisory"])

@router.post("/advisory", response_model=FarmerAdvisoryResponse)
def get_farmer_crop_advisory(req: FarmerAdvisoryRequest):
    """
    Computes crop weather suitability (0-100), irrigation suggestions,
    and stage-specific advisories based on weather, soil moisture, and forecast.
    """
    return generate_farmer_advisory(req)
