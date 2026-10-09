"""
Dashboard statistics and chart analytics routes for Customer view.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from backend.extensions import db
from backend.models import Alert, Transaction, User

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user or not user.account:
        return jsonify({'error': 'User account not found.'}), 404

    txns = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).all()
    alerts = Alert.query.filter_by(user_id=user.id).order_by(Alert.created_at.desc()).all()

    total_count = len(txns)
    successful_count = sum(1 for t in txns if t.status == 'SUCCESS')
    suspicious_count = sum(1 for t in txns if t.risk_level == 'MEDIUM_RISK' or t.status == 'FLAGGED_FOR_VERIFICATION')
    fraudulent_count = sum(1 for t in txns if t.risk_level == 'HIGH_RISK' or t.status == 'BLOCKED')

    avg_risk_score = round(sum(t.risk_score for t in txns) / (total_count or 1), 2)
    total_spent = sum(t.amount for t in txns if t.status in ('SUCCESS', 'FLAGGED_FOR_VERIFICATION'))

    # Current risk status badge
    if fraudulent_count > 0 or any(a.severity == 'HIGH' and a.alert_status == 'ACTIVE' for a in alerts):
        current_risk_status = 'HIGH_ALERT'
    elif suspicious_count > 0:
        current_risk_status = 'MODERATE_MONITORED'
    else:
        current_risk_status = 'SECURE'

    return jsonify({
        'user': user.to_dict(),
        'account': user.account.to_dict(),
        'metrics': {
            'total_transactions': total_count,
            'successful_transactions': successful_count,
            'suspicious_transactions': suspicious_count,
            'fraudulent_transactions': fraudulent_count,
            'total_spent': round(total_spent, 2),
            'available_balance': user.account.balance,
            'average_risk_score': avg_risk_score,
            'active_alerts': sum(1 for a in alerts if a.alert_status == 'ACTIVE'),
            'current_risk_status': current_risk_status
        },
        'recent_transactions': [t.to_dict() for t in txns[:6]],
        'recent_alerts': [a.to_dict() for a in alerts[:4]]
    }), 200


@dashboard_bp.route('/charts', methods=['GET'])
@jwt_required()
def get_dashboard_charts():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    txns = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.asc()).all()

    # 1. Transactions Over Time (by date)
    date_spending = defaultdict(float)
    date_counts = defaultdict(int)
    for t in txns:
        d_str = t.timestamp.strftime('%Y-%m-%d')
        date_spending[d_str] += t.amount
        date_counts[d_str] += 1

    time_labels = sorted(date_spending.keys()) if date_spending else [datetime.utcnow().strftime('%Y-%m-%d')]
    spending_series = [round(date_spending[d], 2) for d in time_labels]
    count_series = [date_counts[d] for d in time_labels]

    # 2. Legitimate vs Fraudulent vs Suspicious Breakdown
    legit_count = sum(1 for t in txns if t.risk_level == 'LOW_RISK')
    suspicious_count = sum(1 for t in txns if t.risk_level == 'MEDIUM_RISK')
    fraud_count = sum(1 for t in txns if t.risk_level == 'HIGH_RISK')

    # 3. Risk Level Distribution (Buckets: 0-30, 31-70, 71-100)
    risk_distribution = {
        'Low Risk (0-30)': legit_count,
        'Medium Risk (31-70)': suspicious_count,
        'High Risk (71-100)': fraud_count
    }

    # 4. Spending by Category / Transaction Type
    cat_spending = defaultdict(float)
    for t in txns:
        cat_spending[t.transaction_type or 'P2P'] += t.amount

    return jsonify({
        'timeline': {
            'labels': time_labels,
            'spending': spending_series,
            'counts': count_series
        },
        'status_breakdown': {
            'labels': ['Legitimate', 'Suspicious', 'Fraudulent'],
            'data': [legit_count, suspicious_count, fraud_count]
        },
        'risk_distribution': risk_distribution,
        'category_distribution': {
            'labels': list(cat_spending.keys()),
            'data': [round(v, 2) for v in cat_spending.values()]
        }
    }), 200
