"""
train.py - Machine Learning Pipeline for WeatherGPT
SIH 2026 Problem Statement SIH26068

Trains:
1. Multi-class Weather Risk Classifier (LOW, MODERATE, HIGH, SEVERE)
2. Continuous Risk Score Regressor (0 - 100)

Evaluates:
- Random Forest vs HistGradientBoosting
- Time-aware chronological train-test split (Zero future leakage)
- Real calculated metrics (Accuracy, Precision, Recall, Macro F1, Confusion Matrix)
- Feature Importance ranking
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report, mean_absolute_error, r2_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "ml_training_dataset.csv")
MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
ROOT_MODELS_DIR = os.path.join(BASE_DIR, "models")

FEATURE_COLS = [
    "temperature_mean",
    "temperature_max",
    "temperature_min",
    "humidity_mean",
    "humidity_max",
    "wind_speed",
    "wind_gust",
    "surface_pressure",
    "precipitation",
    "rainfall_1d",
    "rainfall_3d",
    "rainfall_7d",
    "rainfall_30d",
    "rainfall_climatology",
    "rainfall_anomaly",
    "rainfall_anomaly_percent",
    "temperature_change_24h",
    "rainfall_change_24h",
    "soil_moisture",
    "latitude",
    "longitude",
    "month",
    "day_of_year"
]

SEASON_MAPPING = {
    "Winter": 0,
    "Summer": 1,
    "Monsoon": 2,
    "Post-Monsoon": 3
}

def load_and_preprocess_data():
    """Loads dataset and performs time-aware train/test split."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Training dataset not found at {DATA_PATH}")
    
    df = pd.read_csv(DATA_PATH)
    # Ensure chronological sorting
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Map season to numeric
    df['season_code'] = df['season'].map(SEASON_MAPPING).fillna(0).astype(int)
    features = FEATURE_COLS + ["season_code"]
    
    X = df[features]
    y_class = df["weather_risk_level"].astype(int)
    y_score = df["risk_score"].astype(float)
    
    # Time-aware split: 80% train, 20% test
    split_idx = int(len(df) * 0.80)
    
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train_c, y_test_c = y_class.iloc[:split_idx], y_class.iloc[split_idx:]
    y_train_s, y_test_s = y_score.iloc[:split_idx], y_score.iloc[split_idx:]
    
    train_dates = (df['date'].iloc[0].strftime('%Y-%m-%d'), df['date'].iloc[split_idx-1].strftime('%Y-%m-%d'))
    test_dates = (df['date'].iloc[split_idx].strftime('%Y-%m-%d'), df['date'].iloc[-1].strftime('%Y-%m-%d'))
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return {
        "X_train": X_train,
        "X_test": X_test,
        "X_train_scaled": X_train_scaled,
        "X_test_scaled": X_test_scaled,
        "y_train_c": y_train_c,
        "y_test_c": y_test_c,
        "y_train_s": y_train_s,
        "y_test_s": y_test_s,
        "features": features,
        "scaler": scaler,
        "train_dates": train_dates,
        "test_dates": test_dates
    }

def train_and_evaluate():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(ROOT_MODELS_DIR, exist_ok=True)
    
    print("[INFO] Loading and preprocessing data with time-aware splitting...")
    data = load_and_preprocess_data()
    
    print(f" -> Train period: {data['train_dates'][0]} to {data['train_dates'][1]} ({len(data['X_train'])} samples)")
    print(f" -> Test period:  {data['test_dates'][0]} to {data['test_dates'][1]} ({len(data['X_test'])} samples)")
    
    # 1. Train Model 1: Random Forest Classifier
    print("\n[INFO] Training Model 1: Random Forest Classifier...")
    rf_clf = RandomForestClassifier(n_estimators=120, max_depth=14, min_samples_split=4, random_state=42, n_jobs=-1)
    rf_clf.fit(data["X_train"], data["y_train_c"])
    rf_preds = rf_clf.predict(data["X_test"])
    
    rf_acc = accuracy_score(data["y_test_c"], rf_preds)
    rf_f1 = f1_score(data["y_test_c"], rf_preds, average="macro")
    print(f"  -> Random Forest Test Accuracy: {rf_acc:.4f} | Macro F1: {rf_f1:.4f}")
    
    # 2. Train Model 2: HistGradientBoosting Classifier
    print("\n[INFO] Training Model 2: HistGradientBoosting Classifier...")
    hgb_clf = HistGradientBoostingClassifier(max_iter=150, max_depth=8, random_state=42)
    hgb_clf.fit(data["X_train"], data["y_train_c"])
    hgb_preds = hgb_clf.predict(data["X_test"])
    
    hgb_acc = accuracy_score(data["y_test_c"], hgb_preds)
    hgb_f1 = f1_score(data["y_test_c"], hgb_preds, average="macro")
    print(f"  -> HistGradientBoosting Test Accuracy: {hgb_acc:.4f} | Macro F1: {hgb_f1:.4f}")
    
    # Select Best Classifier based on Macro F1
    if rf_f1 >= hgb_f1:
        best_clf = rf_clf
        best_name = "RandomForestClassifier"
        best_preds = rf_preds
        best_acc = rf_acc
        best_f1 = rf_f1
    else:
        best_clf = hgb_clf
        best_name = "HistGradientBoostingClassifier"
        best_preds = hgb_preds
        best_acc = hgb_acc
        best_f1 = hgb_f1
        
    print(f"\n[OK] Selected Champion Model: {best_name} (Accuracy: {best_acc*100:.2f}%, Macro F1: {best_f1*100:.2f}%)")
    
    # 3. Train Risk Score Regressor (Continuous 0-100)
    print("\n[INFO] Training Risk Score Regressor...")
    rf_reg = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    rf_reg.fit(data["X_train"], data["y_train_s"])
    reg_preds = rf_reg.predict(data["X_test"])
    reg_mae = mean_absolute_error(data["y_test_s"], reg_preds)
    reg_r2 = r2_score(data["y_test_s"], reg_preds)
    print(f"  -> Risk Score Regressor MAE: {reg_mae:.2f} points | R2 Score: {reg_r2:.4f}")
    
    # Detailed Evaluation Metrics
    precision_macro = precision_score(data["y_test_c"], best_preds, average="macro", zero_division=0)
    recall_macro = recall_score(data["y_test_c"], best_preds, average="macro", zero_division=0)
    precision_weighted = precision_score(data["y_test_c"], best_preds, average="weighted", zero_division=0)
    recall_weighted = recall_score(data["y_test_c"], best_preds, average="weighted", zero_division=0)
    f1_weighted = f1_score(data["y_test_c"], best_preds, average="weighted", zero_division=0)
    cm = confusion_matrix(data["y_test_c"], best_preds).tolist()
    clf_report = classification_report(data["y_test_c"], best_preds, target_names=["LOW (0)", "MODERATE (1)", "HIGH (2)", "SEVERE (3)"], output_dict=True)
    
    # Feature Importances (From Random Forest)
    importances = rf_clf.feature_importances_
    feat_imp = sorted(
        [{"feature": f, "importance": round(float(imp), 4)} for f, imp in zip(data["features"], importances)],
        key=lambda x: x["importance"],
        reverse=True
    )
    
    print("\n[INFO] Top 7 Primary Weather Risk Features:")
    for f in feat_imp[:7]:
        print(f"  * {f['feature']:<25}: {f['importance']*100:.2f}%")
        
    # Save Model Artifacts
    model_bundle = {
        "classifier": best_clf,
        "regressor": rf_reg,
        "features": data["features"],
        "season_mapping": SEASON_MAPPING,
        "model_name": best_name
    }
    
    clf_path = os.path.join(MODELS_DIR, "weather_risk_model.pkl")
    root_clf_path = os.path.join(ROOT_MODELS_DIR, "weather_risk_model.pkl")
    joblib.dump(model_bundle, clf_path)
    joblib.dump(model_bundle, root_clf_path)
    
    prep_path = os.path.join(MODELS_DIR, "preprocessor.pkl")
    root_prep_path = os.path.join(ROOT_MODELS_DIR, "preprocessor.pkl")
    joblib.dump(data["scaler"], prep_path)
    joblib.dump(data["scaler"], root_prep_path)
    
    metadata = {
        "model_name": best_name,
        "training_date": datetime.now().isoformat(),
        "algorithm_family": "Ensemble Decision Trees (Scikit-Learn)",
        "features": data["features"],
        "feature_importance_ranking": feat_imp,
        "targets": {
            "classification": "weather_risk_level (0=LOW, 1=MODERATE, 2=HIGH, 3=SEVERE)",
            "regression": "risk_score (0.0 to 100.0 continuous)"
        },
        "evaluation_metrics": {
            "accuracy": round(best_acc, 4),
            "macro_f1": round(best_f1, 4),
            "macro_precision": round(precision_macro, 4),
            "macro_recall": round(recall_macro, 4),
            "weighted_f1": round(f1_weighted, 4),
            "weighted_precision": round(precision_weighted, 4),
            "weighted_recall": round(recall_weighted, 4),
            "confusion_matrix": cm,
            "classification_report": clf_report,
            "regressor_mae": round(reg_mae, 2),
            "regressor_r2": round(reg_r2, 4)
        },
        "data_provenance": {
            "training_samples": len(data["X_train"]),
            "test_samples": len(data["X_test"]),
            "split_type": "Time-Aware Chronological Split (Zero Future Leakage)",
            "dataset_type": "Synthetic Demonstration Labels (Multi-hazard Physics Simulation) + Authentic Meteorological Features",
            "honesty_disclaimer": "Prototype model trained using synthetic demonstration labels + available real weather features. Verify with official authorities for emergency decisions."
        }
    }
    
    meta_path = os.path.join(MODELS_DIR, "model_metadata.json")
    root_meta_path = os.path.join(ROOT_MODELS_DIR, "model_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    with open(root_meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"\n[OK] Model bundle saved to: {clf_path}")
    print(f"[OK] Preprocessor saved to: {prep_path}")
    print(f"[OK] Model metadata saved to: {meta_path}")

if __name__ == "__main__":
    train_and_evaluate()
