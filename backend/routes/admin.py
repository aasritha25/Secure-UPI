"""
Admin operations, monitoring, filtering, and enterprise analytics routes for Secure UPI.
Protected by RBAC admin_required decorator.
"""

from collections import defaultdict
from datetime import datetime
from flask import Blueprint, jsonify, request
from backend.models import Alert, Transaction, User
from backend.utils.security import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/users', methods=['GET'])
@admin_required()
def get_all_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({
        'total_users': len(users),
        'users': [u.to_dict() for u in users]
    }), 200


@admin_bp.route('/transactions', methods=['GET'])
@admin_required()
def get_all_transactions():
    query = Transaction.query

    # Filters
    status = request.args.get('status')
    if status and status.lower() != 'all':
        query = query.filter_by(status=status.upper())

    risk_level = request.args.get('risk_level')
    if risk_level and risk_level.lower() != 'all':
        query = query.filter_by(risk_level=risk_level.upper())

    location = request.args.get('location')
    if location and location.lower() != 'all':
        query = query.filter(Transaction.location.ilike(f"%{location}%"))

    user_query = request.args.get('user')
    if user_query:
        query = query.join(User).filter(
            (User.name.ilike(f"%{user_query}%")) | 
            (User.email.ilike(f"%{user_query}%")) |
            (Transaction.user_id == user_query if user_query.isdigit() else False)
        )

    min_amount = request.args.get('min_amount')
    if min_amount:
        try:
            query = query.filter(Transaction.amount >= float(min_amount))
        except ValueError:
            pass

    max_amount = request.args.get('max_amount')
    if max_amount:
        try:
            query = query.filter(Transaction.amount <= float(max_amount))
        except ValueError:
            pass

    date_from = request.args.get('date_from')
    if date_from:
        try:
            df = datetime.fromisoformat(date_from)
            query = query.filter(Transaction.timestamp >= df)
        except ValueError:
            pass

    date_to = request.args.get('date_to')
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            query = query.filter(Transaction.timestamp <= dt)
        except ValueError:
            pass

    txns = query.order_by(Transaction.timestamp.desc()).all()
    return jsonify({
        'count': len(txns),
        'transactions': [t.to_dict() for t in txns]
    }), 200


@admin_bp.route('/alerts', methods=['GET'])
@admin_required()
def get_all_alerts():
    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    return jsonify({
        'total_alerts': len(alerts),
        'active_alerts': sum(1 for a in alerts if a.alert_status == 'ACTIVE'),
        'alerts': [a.to_dict() for a in alerts]
    }), 200


@admin_bp.route('/stats', methods=['GET'])
@admin_required()
def get_admin_stats():
    users = User.query.all()
    txns = Transaction.query.order_by(Transaction.timestamp.asc()).all()
    alerts = Alert.query.all()

    total_txns = len(txns)
    legit_count = sum(1 for t in txns if t.risk_level == 'LOW_RISK')
    suspicious_count = sum(1 for t in txns if t.risk_level == 'MEDIUM_RISK')
    fraud_count = sum(1 for t in txns if t.risk_level == 'HIGH_RISK')
    blocked_count = sum(1 for t in txns if t.status == 'BLOCKED')
    high_risk_count = sum(1 for t in txns if t.risk_level == 'HIGH_RISK')
    
    total_volume = sum(t.amount for t in txns if t.status in ('SUCCESS', 'FLAGGED_FOR_VERIFICATION'))
    fraud_volume_intercepted = sum(t.amount for t in txns if t.status == 'BLOCKED')

    fraud_pct = round((fraud_count / (total_txns or 1)) * 100, 2)
    suspicious_pct = round((suspicious_count / (total_txns or 1)) * 100, 2)
    avg_risk = round(sum(t.risk_score for t in txns) / (total_txns or 1), 2)

    # Trends over time
    daily_stats = defaultdict(lambda: {'legit': 0, 'suspicious': 0, 'fraud': 0, 'amount': 0.0})
    for t in txns:
        d = t.timestamp.strftime('%Y-%m-%d')
        if t.risk_level == 'LOW_RISK':
            daily_stats[d]['legit'] += 1
        elif t.risk_level == 'MEDIUM_RISK':
            daily_stats[d]['suspicious'] += 1
        else:
            daily_stats[d]['fraud'] += 1
        daily_stats[d]['amount'] += t.amount

    timeline_labels = sorted(daily_stats.keys()) if daily_stats else [datetime.utcnow().strftime('%Y-%m-%d')]
    legit_trend = [daily_stats[d]['legit'] for d in timeline_labels]
    suspicious_trend = [daily_stats[d]['suspicious'] for d in timeline_labels]
    fraud_trend = [daily_stats[d]['fraud'] for d in timeline_labels]

    # Location breakdown
    location_counts = defaultdict(int)
    for t in txns:
        location_counts[t.location or 'Unknown'] += 1

    return jsonify({
        'kpis': {
            'total_users': len(users),
            'total_transactions': total_txns,
            'legitimate_transactions': legit_count,
            'suspicious_transactions': suspicious_count,
            'fraudulent_transactions': fraud_count,
            'high_risk_transactions': high_risk_count,
            'blocked_transactions': blocked_count,
            'total_alerts': len(alerts),
            'active_alerts': sum(1 for a in alerts if a.alert_status == 'ACTIVE'),
            'fraud_percentage': fraud_pct,
            'suspicious_percentage': suspicious_pct,
            'average_risk_score': avg_risk,
            'total_volume_inr': round(total_volume, 2),
            'fraud_volume_intercepted_inr': round(fraud_volume_intercepted, 2)
        },
        'charts': {
            'timeline': {
                'labels': timeline_labels,
                'legitimate': legit_trend,
                'suspicious': suspicious_trend,
                'fraudulent': fraud_trend
            },
            'risk_pie': {
                'labels': ['Legitimate (0-30)', 'Suspicious (31-70)', 'High Risk / Fraud (71-100)'],
                'data': [legit_count, suspicious_count, fraud_count]
            },
            'location_distribution': {
                'labels': list(location_counts.keys()),
                'data': list(location_counts.values())
            }
        }
    }), 200
