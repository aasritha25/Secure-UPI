"""
Fraud Detection Service orchestrating real-time ML scoring and risk classification.
"""

from typing import Any, Dict
from backend.ml.predict import FraudPredictor
from backend.models import User
from backend.services.feature_extractor import extract_features_for_transaction


class FraudDetectionService:
    def __init__(self):
        self.predictor = FraudPredictor()

    def analyze_transaction(self, user: User, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Extract dynamic & simulated features
        features = extract_features_for_transaction(user, payload)
        
        # Execute prediction
        result = self.predictor.predict_transaction(features)
        result['extracted_features'] = features
        return result

    def get_model_metrics(self) -> Dict[str, Any]:
        return self.predictor.get_model_metrics()
