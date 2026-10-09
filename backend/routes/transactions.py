"""
Transaction management routes for Secure UPI.
Handles payment initiation, ML fraud checking, balance deduction, and transaction history.
"""

import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from backend.extensions import db
from backend.models import Account, FraudPrediction, Transaction, User
from backend.services.alert_service import create_fraud_alert
from backend.services.fraud_detector import FraudDetectionService
from backend.utils.validators import validate_transaction_payload

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')
fraud_service = FraudDetectionService()


@transactions_bp.route('', methods=['POST'])
@jwt_required()
def create_transaction():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user or not user.account:
        return jsonify({'error': 'Active account not found for this user.'}), 404

    payload = request.get_json(silent=True) or {}
    is_valid, err_msg = validate_transaction_payload(payload)
    if not is_valid:
        return jsonify({'error': err_msg}), 400

    amount = float(payload['amount'])
    receiver_id = str(payload['receiver_id']).strip()
    receiver_name = str(payload.get('receiver_name', receiver_id)).strip()
    txn_type = str(payload.get('transaction_type', 'P2P')).upper()
    location = str(payload.get('location', 'Hyderabad')).strip()
    device_id = str(payload.get('device_id', 'DEV_ANDROID_14_HYD')).strip()
    ip_address = request.remote_addr or '127.0.0.1'
    note = str(payload.get('note', '')).strip()

    # 1. Run Real-Time ML Fraud Detection
    analysis = fraud_service.analyze_transaction(user, payload)
    fraud_prob = analysis['fraud_probability']
    risk_score = analysis['risk_score']
    risk_level = analysis['risk_level'] # LOW_RISK, MEDIUM_RISK, HIGH_RISK
    prediction = analysis['prediction'] # Legitimate, Suspicious, Fraudulent
    reasons = analysis['reasons']
    contributions = analysis['feature_contributions']

    # 2. Determine Transaction Status & Balance Handling
    account = user.account
    if risk_level == 'HIGH_RISK':
        # Automatically block high-risk fraudulent transaction
        status = 'BLOCKED'
        message = 'High-risk fraudulent transaction intercepted and blocked by ML Security Engine.'
    elif amount > account.balance:
        status = 'FAILED'
        message = f"Transaction failed: Insufficient balance (Available: ₹{account.balance:,.2f})."
    elif risk_level == 'MEDIUM_RISK':
        # Suspicious transaction: Allow simulation or step-up verification
        # For academic simulation, if explicitly confirmed or completed
        account.balance -= amount
        status = 'FLAGGED_FOR_VERIFICATION'
        message = 'Transaction processed with suspicious activity flag. Verification alert created.'
    else:
        # Legitimate transaction: Deduct balance and approve
        account.balance -= amount
        status = 'SUCCESS'
        message = 'Transaction completed successfully.'

    account.updated_at = datetime.utcnow()

    # 3. Persist Transaction Record
    txn = Transaction(
        user_id=user.id,
        receiver_id=receiver_id,
        receiver_name=receiver_name,
        amount=amount,
        location=location,
        device_id=device_id,
        ip_address=ip_address,
        transaction_type=txn_type,
        status=status,
        risk_score=risk_score,
        risk_level=risk_level,
        fraud_probability=fraud_prob,
        prediction=prediction,
        note=note,
        timestamp=datetime.utcnow()
    )
    db.session.add(txn)
    db.session.flush()

    # 4. Persist Fraud Prediction & Explainability
    fp = FraudPrediction(
        transaction_id=txn.transaction_id,
        user_id=user.id,
        model_name=analysis['model_used'],
        fraud_probability=fraud_prob,
        risk_score=risk_score,
        risk_level=risk_level,
        prediction=prediction,
        explanation=json.dumps(reasons),
        feature_contributions=json.dumps(contributions),
        created_at=datetime.utcnow()
    )
    db.session.add(fp)

    # 5. Generate Fraud Alert if required
    alert = None
    if risk_level in ('MEDIUM_RISK', 'HIGH_RISK'):
        alert = create_fraud_alert(user, txn, risk_level, reasons, risk_score)

    db.session.commit()

    return jsonify({
        'message': message,
        'transaction_status': prediction,
        'status': status,
        'fraud_probability': fraud_prob,
        'risk_score': risk_score,
        'risk_level': risk_level,
        'recommendation': analysis['recommendation'],
        'reasons': reasons,
        'transaction': txn.to_dict(),
        'remaining_balance': account.balance,
        'alert_created': alert is not None
    }), 201


@transactions_bp.route('', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = get_jwt_identity()
    query = Transaction.query.filter_by(user_id=user_id)

    # Optional status filter
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status.upper())

    # Optional risk_level filter
    risk_level = request.args.get('risk_level')
    if risk_level:
        query = query.filter_by(risk_level=risk_level.upper())

    rows = query.order_by(Transaction.timestamp.desc()).all()
    return jsonify({
        'count': len(rows),
        'transactions': [t.to_dict() for t in rows]
    }), 200


@transactions_bp.route('/<transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction_detail(transaction_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    # Admins can view any transaction, customers only view their own
    if user.role == 'admin':
        txn = Transaction.query.filter(
            (Transaction.id == transaction_id) | (Transaction.transaction_id == transaction_id)
        ).first()
    else:
        txn = Transaction.query.filter(
            ((Transaction.id == transaction_id) | (Transaction.transaction_id == transaction_id)),
            Transaction.user_id == user.id
        ).first()

    if not txn:
        return jsonify({'error': 'Transaction not found.'}), 404

    pred_record = txn.prediction_record.to_dict() if txn.prediction_record else None
    return jsonify({
        'transaction': txn.to_dict(),
        'analysis': pred_record
    }), 200
