"""
Model performance and comparative metrics routes for Secure UPI.
Returns actual metrics obtained during training for Logistic Regression, Random Forest, and XGBoost.
"""

from flask import Blueprint, jsonify
from backend.services.fraud_detector import FraudDetectionService

model_metrics_bp = Blueprint('model_metrics', __name__, url_prefix='/api/model')
fraud_service = FraudDetectionService()


@model_metrics_bp.route('/metrics', methods=['GET'])
def get_metrics():
    metrics_data = fraud_service.get_model_metrics()
    return jsonify(metrics_data), 200
