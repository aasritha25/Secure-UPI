import json
import os
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODEL_PATH = os.path.join(MODEL_DIR, 'fraud_model.joblib')
METRICS_PATH = os.path.join(MODEL_DIR, 'fraud_model_metrics.json')

FEATURE_COLUMNS = [
    'amount',
    'transaction_frequency',
    'average_amount',
    'time_since_last_transaction',
    'device_new',
    'location_change',
    'account_age_days',
    'failed_transactions',
    'transaction_velocity',
    'time_of_day',
    'is_known_receiver',
]


class FraudRiskModel:
    def __init__(self):
        self.model = None
        self.metrics = {
            'accuracy': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0,
            'roc_auc': 0.0,
            'confusion_matrix': [0, 0, 0, 0],
        }
        self._load_or_train()

    def _generate_synthetic_dataset(self):
        rng = np.random.default_rng(42)
        rows = []

        for _ in range(1500):
            amount = float(rng.integers(100, 120000, endpoint=True))
            avg_amount = float(rng.integers(150, 8000, endpoint=True))
            transaction_frequency = float(rng.integers(1, 25))
            time_since_last_transaction = float(rng.integers(1, 360))
            device_new = int(rng.random() < 0.28)
            location_change = int(rng.random() < 0.22)
            account_age_days = float(rng.integers(30, 1800, endpoint=True))
            failed_transactions = int(rng.integers(0, 8))
            transaction_velocity = float(rng.integers(1, 12))
            time_of_day = float(rng.integers(0, 23))
            is_known_receiver = int(rng.random() < 0.72)

            risk_score = (
                (amount / max(avg_amount, 1)) * 0.35
                + transaction_frequency * 0.08
                + device_new * 0.65
                + location_change * 0.55
                + (failed_transactions / 8.0) * 0.4
                + (time_since_last_transaction < 30) * 0.15
                + (amount > avg_amount * 6) * 0.9
                + (transaction_velocity > 7) * 0.35
            )

            is_fraud = int(risk_score > 1.1 or (rng.random() < 0.04 and amount > 40000))
            if is_fraud:
                amount = float(max(amount, avg_amount * 4))
                device_new = int(1 if rng.random() < 0.8 else device_new)
                location_change = int(1 if rng.random() < 0.75 else location_change)
             
            rows.append({
                'amount': amount,
                'transaction_frequency': transaction_frequency,
                'average_amount': avg_amount,
                'time_since_last_transaction': time_since_last_transaction,
                'device_new': device_new,
                'location_change': location_change,
                'account_age_days': account_age_days,
                'failed_transactions': failed_transactions,
                'transaction_velocity': transaction_velocity,
                'time_of_day': time_of_day,
                'is_known_receiver': is_known_receiver,
                'is_fraud': is_fraud,
            })

        return pd.DataFrame(rows)

    def _save_model(self):
        if self.model is None:
            return
        joblib.dump(self.model, MODEL_PATH)
        with open(METRICS_PATH, 'w', encoding='utf-8') as fh:
            json.dump(self.metrics, fh)

    def _load_or_train(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(METRICS_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                with open(METRICS_PATH, 'r', encoding='utf-8') as fh:
                    self.metrics = json.load(fh)
                return
            except Exception:
                pass

        self.train()

    def train(self):
        df = self._generate_synthetic_dataset()
        X = df[FEATURE_COLUMNS]
        y = df['is_fraud']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        log_model = LogisticRegression(max_iter=2000, random_state=42)
        rf_model = RandomForestClassifier(n_estimators=250, random_state=42, class_weight='balanced_subsample')

        log_model.fit(X_train, y_train)
        rf_model.fit(X_train, y_train)

        avg_proba = (log_model.predict_proba(X_test)[:, 1] + rf_model.predict_proba(X_test)[:, 1]) / 2.0
        y_pred = (avg_proba >= 0.5).astype(int)

        self.model = {'logistic_regression': log_model, 'random_forest': rf_model}
        self.metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, zero_division=0)),
            'recall': float(recall_score(y_test, y_pred, zero_division=0)),
            'f1_score': float(f1_score(y_test, y_pred, zero_division=0)),
            'roc_auc': float(roc_auc_score(y_test, avg_proba)),
            'confusion_matrix': [int(v) for v in confusion_matrix(y_test, y_pred).ravel()],
        }

        self._save_model()

    def predict_probability(self, payload: Dict[str, float]):
        if self.model is None:
            self.train()

        row = pd.DataFrame([payload], columns=FEATURE_COLUMNS)
        lr_prob = float(self.model['logistic_regression'].predict_proba(row)[0, 1])
        rf_prob = float(self.model['random_forest'].predict_proba(row)[0, 1])
        return float(np.clip((lr_prob + rf_prob) / 2.0, 0.0, 1.0))

    def health(self):
        return {
            'status': 'ready',
            'model_types': ['logistic_regression', 'random_forest'],
            'metrics': self.metrics,
        }
