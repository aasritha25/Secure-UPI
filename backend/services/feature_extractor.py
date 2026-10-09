"""
Feature Extraction Service for Secure UPI.
Extracts user transaction baseline metrics and transforms live transaction requests
into feature vectors required by the ML model.
"""

from datetime import datetime
from typing import Any, Dict
from backend.models import Transaction, User


def extract_features_for_transaction(user: User, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes dynamic baseline features from user history and incoming transaction payload.
    Supports overrides from simulated inputs for testing different fraud scenarios.
    """
    # Fetch user's previous transactions
    past_txns = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).all()
    
    # 1. Historical Average Amount
    if 'average_amount' in payload and float(payload['average_amount']) > 0:
        avg_amount = float(payload['average_amount'])
    elif past_txns:
        successful_past = [t.amount for t in past_txns if t.status in ('SUCCESS', 'FLAGGED_FOR_VERIFICATION')]
        avg_amount = float(sum(successful_past) / len(successful_past)) if successful_past else float(payload.get('amount', 1000.0))
    else:
        avg_amount = float(payload.get('amount', 1000.0))

    # 2. Transaction Frequency
    if 'transaction_frequency' in payload:
        txn_frequency = float(payload['transaction_frequency'])
    else:
        txn_frequency = float(len(past_txns) if past_txns else 1.0)

    # 3. Time Since Last Transaction (in minutes)
    if 'time_since_last_transaction' in payload:
        time_since_last = float(payload['time_since_last_transaction'])
    elif past_txns:
        last_time = past_txns[0].timestamp
        diff_mins = (datetime.utcnow() - last_time).total_seconds() / 60.0
        time_since_last = max(0.5, round(diff_mins, 1))
    else:
        time_since_last = 120.0

    # 4. Device Change / Novelty
    current_device = str(payload.get('device_id', 'DEV_ANDROID_14_HYD')).strip()
    if 'device_new' in payload:
        device_new = int(payload['device_new'])
    elif past_txns:
        known_devices = {t.device_id for t in past_txns if t.device_id}
        device_new = 1 if current_device not in known_devices else 0
    else:
        device_new = 0

    # 5. Location Change / Novelty
    current_location = str(payload.get('location', 'Hyderabad')).strip()
    if 'location_change' in payload:
        location_change = int(payload['location_change'])
    elif past_txns:
        last_location = past_txns[0].location
        location_change = 1 if last_location and last_location.lower() != current_location.lower() else 0
    else:
        location_change = 0

    # 6. Account Age in Days
    if 'account_age_days' in payload:
        account_age = float(payload['account_age_days'])
    else:
        account_age = max(1.0, float((datetime.utcnow() - user.created_at).days) + 30.0)

    # 7. Failed Transactions
    if 'failed_transactions' in payload:
        failed_count = int(payload['failed_transactions'])
    elif past_txns:
        failed_count = sum(1 for t in past_txns[:5] if t.status == 'FAILED')
    else:
        failed_count = 0

    # 8. Transaction Velocity (transactions per hour / burst measure)
    if 'transaction_velocity' in payload:
        velocity = float(payload['transaction_velocity'])
    else:
        velocity = float(min(12.0, max(0.5, (txn_frequency / 4.0))))

    # 9. Time of Day (Hour 0 - 23)
    if 'time_of_day' in payload:
        time_of_day = int(payload['time_of_day'])
    else:
        time_of_day = int(datetime.utcnow().hour)

    # 10. Known Receiver
    receiver_id = str(payload.get('receiver_id', '')).strip()
    if 'is_known_receiver' in payload:
        is_known_receiver = int(payload['is_known_receiver'])
    elif past_txns:
        known_receivers = {t.receiver_id for t in past_txns}
        is_known_receiver = 1 if receiver_id in known_receivers else 0
    else:
        is_known_receiver = 0

    # 11. Transaction Type
    txn_type = str(payload.get('transaction_type', 'P2P')).upper()

    return {
        'amount': float(payload.get('amount', 0.0)),
        'average_amount': avg_amount,
        'transaction_frequency': txn_frequency,
        'time_since_last_transaction': time_since_last,
        'time_of_day': time_of_day,
        'location_change': location_change,
        'device_new': device_new,
        'account_age_days': account_age,
        'failed_transactions': failed_count,
        'transaction_velocity': velocity,
        'is_known_receiver': is_known_receiver,
        'transaction_type': txn_type,
        'location': current_location,
        'device_id': current_device,
        'ip_address': str(payload.get('ip_address', '127.0.0.1'))
    }
