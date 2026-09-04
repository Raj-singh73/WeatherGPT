"""
evaluate.py - Standalone Model Evaluation & Honesty Verification Module
SIH 2026 Problem Statement SIH26068
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METADATA_PATH = os.path.join(BASE_DIR, "ml", "models", "model_metadata.json")

def print_evaluation_summary():
    if not os.path.exists(METADATA_PATH):
        print(f"[ERROR] Metadata not found at {METADATA_PATH}. Please run ml/train.py first.")
        return
        
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    metrics = meta["evaluation_metrics"]
    prov = meta["data_provenance"]
    
    print("\n" + "="*70)
    print("      WEATHERGPT - MODEL EVALUATION & HONESTY AUDIT REPORT")
    print("="*70)
    print(f"Model Champion      : {meta['model_name']}")
    print(f"Algorithm Family    : {meta['algorithm_family']}")
    print(f"Evaluation Split    : {prov['split_type']}")
    print(f"Test Samples        : {prov['test_samples']} observations")
    print(f"Training Samples    : {prov['training_samples']} observations")
    print("-" * 70)
    print(f"Real Test Accuracy  : {metrics['accuracy']*100:.2f}%")
    print(f"Macro F1-Score      : {metrics['macro_f1']*100:.2f}%")
    print(f"Weighted F1-Score   : {metrics['weighted_f1']*100:.2f}%")
    print(f"Macro Precision     : {metrics['macro_precision']*100:.2f}%")
    print(f"Macro Recall        : {metrics['macro_recall']*100:.2f}%")
    print(f"Risk Score MAE      : {metrics['regressor_mae']} points (on 0-100 scale)")
    print(f"Risk Score R2 Score : {metrics['regressor_r2']:.4f}")
    print("-" * 70)
    print("Confusion Matrix (Rows=Actual, Cols=Predicted):")
    labels = ["LOW", "MODERATE", "HIGH", "SEVERE"]
    print(f"{'':<12}" + "".join([f"{l:>12}" for l in labels]))
    for idx, row in enumerate(metrics["confusion_matrix"]):
        print(f"{labels[idx]:<12}" + "".join([f"{val:>12}" for val in row]))
        
    print("-" * 70)
    print("Top 5 Impactful Weather Features:")
    for item in meta["feature_importance_ranking"][:5]:
        print(f"  * {item['feature']:<25}: {item['importance']*100:.2f}% contribution")
        
    print("-" * 70)
    print("SIH HONESTY DISCLAIMER:")
    print(f"\"{prov['honesty_disclaimer']}\"")
    print("="*70 + "\n")

if __name__ == "__main__":
    print_evaluation_summary()
