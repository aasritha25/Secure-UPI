"""
Model Training Script for Secure UPI Fraud Detection.
Trains, evaluates, and compares:
1. Logistic Regression
2. Random Forest
3. XGBoost

Evaluates using: Accuracy, Precision, Recall, F1-Score, ROC-AUC, Confusion Matrix.
Saves the best-performing model and metrics without fabrication.
"""

import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from backend.ml.generate_dataset import generate_upi_dataset
from backend.ml.preprocess import ALL_MODEL_INPUT_COLUMNS, UPIFeaturePipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, 'dataset.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'fraud_model.joblib')
METRICS_PATH = os.path.join(BASE_DIR, 'model_metrics.json')


def load_or_create_dataset():
    if not os.path.exists(DATASET_PATH):
        print("Dataset not found. Generating synthetic UPI dataset...")
        df = generate_upi_dataset(n_samples=10000, random_state=42)
        df.to_csv(DATASET_PATH, index=False)
    else:
        df = pd.read_csv(DATASET_PATH)
    return df


def train_and_evaluate():
    df = load_or_create_dataset()
    print(f"Loaded dataset with {len(df)} records. Fraud count: {df['is_fraud'].sum()} ({df['is_fraud'].mean()*100:.2f}%)")

    X = df[ALL_MODEL_INPUT_COLUMNS]
    y = df['is_fraud']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Fit Preprocessing & Feature Engineering Pipeline
    pipeline = UPIFeaturePipeline()
    X_train_transformed = pipeline.fit_transform(X_train)
    X_test_transformed = pipeline.transform(X_test)
    feature_names = pipeline.get_feature_names()

    # Calculate class imbalance ratio for XGBoost
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = float(neg_count / max(pos_count, 1))

    # Model definitions
    candidate_models = {
        'Logistic Regression': LogisticRegression(
            max_iter=2000,
            class_weight='balanced',
            random_state=42
        ),
        'Random Forest': RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=5,
            class_weight='balanced_subsample',
            random_state=42,
            n_jobs=-1
        )
    }

    if HAS_XGBOOST:
        candidate_models['XGBoost'] = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.08,
            scale_pos_weight=scale_pos_weight,
            eval_metric='logloss',
            random_state=42,
            n_jobs=-1
        )

    results = {}
    trained_models = {}

    print("\n--- Training and Evaluating Models ---")
    for name, model in candidate_models.items():
        print(f"Training {name}...")
        model.fit(X_train_transformed, y_train)
        trained_models[name] = model

        # Predictions & Probabilities
        y_pred = model.predict(X_test_transformed)
        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_test_transformed)[:, 1]
        else:
            y_proba = y_pred

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        roc_auc = float(roc_auc_score(y_test, y_proba))
        cm = [int(v) for v in confusion_matrix(y_test, y_pred).ravel()] # [TN, FP, FN, TP]

        # Feature Importance / Coefficients
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_.tolist()
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_[0]).tolist()
        else:
            importances = [0.0] * len(feature_names)

        results[name] = {
            'accuracy': round(acc, 4),
            'precision': round(prec, 4),
            'recall': round(rec, 4),
            'f1_score': round(f1, 4),
            'roc_auc': round(roc_auc, 4),
            'confusion_matrix': cm,
            'feature_importances': {fn: round(float(imp), 4) for fn, imp in zip(feature_names, importances)}
        }

        print(f"  {name} -> Accuracy: {acc:.4f}, Precision: {prec:.4f}, Recall: {rec:.4f}, F1: {f1:.4f}, ROC-AUC: {roc_auc:.4f}")

    # Select Best Model based on F1-Score & ROC-AUC
    best_model_name = max(results.keys(), key=lambda k: (results[k]['roc_auc'] + results[k]['f1_score']))
    print(f"\nBest Model Selected: {best_model_name}")

    # Package bundle
    model_bundle = {
        'selected_model_name': best_model_name,
        'selected_model': trained_models[best_model_name],
        'all_models': trained_models,
        'pipeline': pipeline,
        'feature_names': feature_names,
        'metrics': results
    }

    joblib.dump(model_bundle, MODEL_PATH)
    print(f"Saved trained model bundle to {MODEL_PATH}")

    # Save detailed JSON metrics for API & Dashboards
    metrics_summary = {
        'dataset_summary': {
            'total_samples': len(df),
            'legitimate_count': int((df['is_fraud'] == 0).sum()),
            'fraudulent_count': int((df['is_fraud'] == 1).sum()),
            'fraud_ratio_pct': round(float(df['is_fraud'].mean() * 100), 2),
            'test_size': len(X_test),
        },
        'selected_model': best_model_name,
        'models': results,
        'feature_names': feature_names,
        'thresholds': {
            'low_risk': [0, 30],
            'medium_risk': [31, 70],
            'high_risk': [71, 100]
        }
    }

    with open(METRICS_PATH, 'w', encoding='utf-8') as f:
        json.dump(metrics_summary, f, indent=2)
    print(f"Saved evaluation metrics to {METRICS_PATH}")

    return model_bundle, metrics_summary


if __name__ == '__main__':
    train_and_evaluate()
