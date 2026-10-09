"""
Model performance and comparative metrics routes for Secure UPI.
Returns actual metrics obtained during training for Logistic Regression, Random Forest, and XGBoost.
"""

from flask import Blueprint, jsonify
from backend.services.fraud_detector import FraudDetectionService

model_metrics_bp = Blueprint('model_metrics', __name__, url_prefix='/api/model')
_fraud_service = None


def _get_fraud_service():
    global _fraud_service
    if _fraud_service is None:
        _fraud_service = FraudDetectionService()
    return _fraud_service


@model_metrics_bp.route('/metrics', methods=['GET'])
def get_metrics():
    metrics_data = _get_fraud_service().get_model_metrics()
    return jsonify(metrics_data), 200
