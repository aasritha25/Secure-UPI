"""
Alert management routes for Secure UPI.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from backend.extensions import db
from backend.models import Alert, User

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')


@alerts_bp.route('', methods=['GET'])
@jwt_required()
def get_alerts():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    # Admins see all alerts, customers see their own
    if user.role == 'admin':
        alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    else:
        alerts = Alert.query.filter_by(user_id=user.id).order_by(Alert.created_at.desc()).all()

    active_count = sum(1 for a in alerts if a.alert_status == 'ACTIVE')
    return jsonify({
        'total_alerts': len(alerts),
        'active_alerts': active_count,
        'alerts': [a.to_dict() for a in alerts]
    }), 200


@alerts_bp.route('/<int:alert_id>/resolve', methods=['PUT', 'POST'])
@jwt_required()
def resolve_alert(alert_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    if user.role == 'admin':
        alert = db.session.get(Alert, alert_id)
    else:
        alert = Alert.query.filter_by(id=alert_id, user_id=user.id).first()

    if not alert:
        return jsonify({'error': 'Alert not found.'}), 404

    payload = request.get_json(silent=True) or {}
    new_status = payload.get('status', 'RESOLVED').upper()
    alert.alert_status = new_status
    db.session.commit()

    return jsonify({
        'message': f'Alert status updated to {new_status}.',
        'alert': alert.to_dict()
    }), 200
