"""
prediction.py - Machine Learning Risk Assessment Endpoint for WeatherGPT
SIH 2026 Problem Statement SIH26068
"""

from fastapi import APIRouter
from models.schemas import RiskPredictionRequest, RiskPredictionResponse
from services.ml_service import predict_custom_risk

router = APIRouter(prefix="/api/predict", tags=["ML Prediction"])

@router.post("/risk", response_model=RiskPredictionResponse)
def predict_risk(req: RiskPredictionRequest):
    """
    Executes ML inference using the trained HistGradientBoosting Champion Model.
    Returns composite Risk Score (0-100), categorical Risk Level, and explainability factors.
    """
    input_data = req.model_dump()
    return predict_custom_risk(input_data)
