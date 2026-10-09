"""
Prediction route for Secure UPI real-time ML risk assessment.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from backend.extensions import db
from backend.models import User
from backend.services.fraud_detector import FraudDetectionService
from backend.utils.validators import validate_transaction_payload

predict_bp = Blueprint('predict', __name__, url_prefix='/api/predict')
fraud_service = FraudDetectionService()


@predict_bp.route('', methods=['POST'])
@jwt_required()
def predict_risk():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    payload = request.get_json(silent=True) or {}
    is_valid, err_msg = validate_transaction_payload(payload)
    if not is_valid:
        return jsonify({'error': err_msg}), 400

    # Execute ML fraud detection
    analysis_result = fraud_service.analyze_transaction(user, payload)

    return jsonify({
        'transaction_status': analysis_result['prediction'], # Legitimate, Suspicious, Fraudulent
        'status': analysis_result['status'], # APPROVED, FLAGGED_FOR_VERIFICATION, BLOCKED
        'fraud_probability': analysis_result['fraud_probability'],
        'risk_score': analysis_result['risk_score'],
        'risk_level': analysis_result['risk_level'],
        'recommendation': analysis_result['recommendation'],
        'reasons': analysis_result['reasons'],
        'feature_contributions': analysis_result['feature_contributions'],
        'model_used': analysis_result['model_used']
    }), 200
