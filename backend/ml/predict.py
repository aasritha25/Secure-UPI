"""
ML Inference & Explainability Service for Secure UPI Fraud Detection.
Loads the trained ML model bundle and provides real-time fraud probability,
risk scores, risk classification, and feature contribution explanations.
"""

import json
import os
from typing import Any, Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd

from backend.ml.preprocess import ALL_MODEL_INPUT_COLUMNS, UPIFeaturePipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'fraud_model.joblib')
METRICS_PATH = os.path.join(BASE_DIR, 'model_metrics.json')


class FraudPredictor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FraudPredictor, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                bundle = joblib.load(MODEL_PATH)
                self.selected_model_name = bundle.get('selected_model_name', 'Random Forest')
                self.selected_model = bundle.get('selected_model')
                self.all_models = bundle.get('all_models', {})
                self.pipeline: UPIFeaturePipeline = bundle.get('pipeline')
                self.feature_names = bundle.get('feature_names', [])
                self.metrics = bundle.get('metrics', {})
            except Exception as e:
                print(f"Warning: Failed to load model bundle: {e}. Will attempt retrain.")
                try:
                    self._train_and_load()
                except Exception as e2:
                    print(f"Warning: Retrain also failed: {e2}. Using fallback.")
                    self._init_fallback()
        else:
            try:
                self._train_and_load()
            except Exception as e:
                print(f"Warning: Training failed (read-only filesystem?): {e}. Using fallback.")
                self._init_fallback()

        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, 'r', encoding='utf-8') as f:
                self.metrics_summary = json.load(f)
        else:
            self.metrics_summary = {'selected_model': self.selected_model_name, 'models': self.metrics}

    def _train_and_load(self):
        from backend.ml.train_model import train_and_evaluate
        bundle, metrics_summary = train_and_evaluate()
        self.selected_model_name = bundle['selected_model_name']
        self.selected_model = bundle['selected_model']
        self.all_models = bundle['all_models']
        self.pipeline = bundle['pipeline']
        self.feature_names = bundle['feature_names']
        self.metrics = bundle['metrics']
        self.metrics_summary = metrics_summary

    def _init_fallback(self):
        """Fallback when model can't be loaded or trained (e.g. read-only Vercel filesystem)."""
        self.selected_model_name = 'Rule-Based Fallback'
        self.selected_model = None
        self.all_models = {}
        self.pipeline = UPIFeaturePipeline()
        self.feature_names = []
        self.metrics = {}
        self.metrics_summary = {'selected_model': 'Rule-Based Fallback', 'models': {}}

    def predict_transaction(self, txn_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes real-time ML fraud prediction and risk scoring.
        """
        # Ensure default input values
        input_dict = {
            'amount': float(txn_data.get('amount', 0.0)),
            'average_amount': float(txn_data.get('average_amount', txn_data.get('amount', 1000.0))),
            'transaction_frequency': float(txn_data.get('transaction_frequency', 5.0)),
            'time_since_last_transaction': float(txn_data.get('time_since_last_transaction', 60.0)),
            'time_of_day': int(txn_data.get('time_of_day', 12)),
            'location_change': int(txn_data.get('location_change', 0)),
            'device_new': int(txn_data.get('device_new', 0)),
            'account_age_days': float(txn_data.get('account_age_days', 180.0)),
            'failed_transactions': int(txn_data.get('failed_transactions', 0)),
            'transaction_velocity': float(txn_data.get('transaction_velocity', 1.0)),
            'is_known_receiver': int(txn_data.get('is_known_receiver', 1)),
            'transaction_type': str(txn_data.get('transaction_type', 'P2P'))
        }

        df_single = pd.DataFrame([input_dict])

        # Get probability from the selected model (or rule-based fallback)
        if self.selected_model is None:
            # Rule-based fallback when ML model is unavailable
            score = 0.0
            if input_dict['amount'] > 25000:
                score += 0.3
            if input_dict['device_new'] == 1:
                score += 0.2
            if input_dict['location_change'] == 1:
                score += 0.2
            if input_dict['failed_transactions'] >= 2:
                score += 0.15
            if input_dict['is_known_receiver'] == 0:
                score += 0.15
            fraud_proba = min(score, 0.99)
        else:
            transformed = self.pipeline.transform(df_single)
            if hasattr(self.selected_model, 'predict_proba'):
                fraud_proba = float(self.selected_model.predict_proba(transformed)[0, 1])
            else:
                pred = self.selected_model.predict(transformed)[0]
                fraud_proba = float(pred)

        # Calculate risk score (0 - 100)
        risk_score = round(float(fraud_proba * 100), 2)

        # Risk Classification (Configurable thresholds: 0-30 Low, 31-70 Medium, 71-100 High)
        if risk_score <= 30.0:
            risk_level = 'LOW_RISK'
            prediction = 'Legitimate'
            status = 'APPROVED'
            recommendation = 'Proceed with normal transaction processing'
        elif risk_score <= 70.0:
            risk_level = 'MEDIUM_RISK'
            prediction = 'Suspicious'
            status = 'FLAGGED_FOR_VERIFICATION'
            recommendation = 'Step-up authentication / OTP verification recommended'
        else:
            risk_level = 'HIGH_RISK'
            prediction = 'Fraudulent'
            status = 'BLOCKED'
            recommendation = 'High risk detected. Transaction blocked and alert generated.'

        # Explainability & Feature Contribution Breakdown
        if self.selected_model is None or not self.feature_names:
            # Fallback: generate reasons from rules only, no feature contributions
            reasons, feature_contributions = self._explain_prediction(input_dict, np.zeros(1), fraud_proba)
        else:
            reasons, feature_contributions = self._explain_prediction(input_dict, transformed[0], fraud_proba)

        return {
            'model_used': self.selected_model_name,
            'fraud_probability': round(fraud_proba, 4),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'prediction': prediction,
            'status': status,
            'recommendation': recommendation,
            'reasons': reasons,
            'feature_contributions': feature_contributions,
            'input_features': input_dict
        }

    def _explain_prediction(self, raw: Dict[str, Any], transformed_vec: np.ndarray, proba: float) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Generates human-readable reasons and feature contribution scores.
        """
        reasons = []
        contributions = []
        avg_amt = max(raw['average_amount'], 1.0)
        amt = raw['amount']
        ratio = amt / avg_amt

        # Feature level checks
        if ratio >= 4.0 or amt >= 35000:
            reasons.append(f"Unusually high transaction amount (₹{amt:,.2f} vs user average ₹{avg_amt:,.2f}, {ratio:.1f}x deviation).")
        
        if raw['device_new'] == 1:
            reasons.append("New/Unrecognized device ID detected for this user account.")

        if raw['location_change'] == 1:
            reasons.append("Unusual geographic location differs from registered primary location.")

        if raw['time_since_last_transaction'] < 5.0 and raw['transaction_velocity'] > 4.0:
            reasons.append(f"Rapid consecutive transaction velocity ({raw['transaction_velocity']:.1f} txns/hr, {raw['time_since_last_transaction']:.1f} mins since previous).")

        if 1 <= raw['time_of_day'] <= 5:
            reasons.append(f"Abnormal transaction timestamp ({raw['time_of_day']:02d}:00 hours - high-risk overnight window).")

        if raw['failed_transactions'] >= 2:
            reasons.append(f"Repeated failed PIN/passcode attempts ({raw['failed_transactions']} previous failures).")

        if raw['is_known_receiver'] == 0 and ratio > 2.0:
            reasons.append("High-value payment directed to a newly added / unverified beneficiary.")

        if not reasons:
            reasons.append("Transaction behavioral pattern aligns with user baseline and normal historical parameters.")

        # Compute feature importance contributions for visualization
        model_importances = self.metrics.get(self.selected_model_name, {}).get('feature_importances', {})
        for idx, fname in enumerate(self.feature_names):
            base_weight = model_importances.get(fname, 0.05)
            # Magnitude of transformation contribution
            feat_val = abs(float(transformed_vec[idx]))
            contribution = round(float(base_weight * (1.0 + feat_val)), 4)
            
            # Format friendly label
            clean_name = fname.replace('_', ' ').title()
            contributions.append({
                'feature': fname,
                'name': clean_name,
                'weight': base_weight,
                'impact': contribution,
                'contribution_level': 'High' if contribution > 0.15 else ('Medium' if contribution > 0.06 else 'Low')
            })

        contributions.sort(key=lambda x: x['impact'], reverse=True)
        return reasons, contributions[:8]

    def get_model_metrics(self) -> Dict[str, Any]:
        return self.metrics_summary
