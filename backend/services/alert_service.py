"""
Alert Service for managing security and fraud notifications.
"""

from typing import List, Optional
from backend.extensions import db
from backend.models import Alert, Transaction, User


def create_fraud_alert(user: User, transaction: Transaction, risk_level: str, reasons: List[str], risk_score: float) -> Optional[Alert]:
    """
    Generates and persists an alert if the transaction is suspicious or high risk.
    """
    if risk_level == 'LOW_RISK':
        return None

    severity = 'HIGH' if risk_level == 'HIGH_RISK' else 'MEDIUM'
    status_label = 'Intercepted & Blocked' if risk_level == 'HIGH_RISK' else 'Flagged for Verification'
    title = f"{'High-Risk' if risk_level == 'HIGH_RISK' else 'Suspicious'} UPI Transaction ({status_label})"
    
    reason_str = " | ".join(reasons) if reasons else "Anomalous transaction behavioral indicators detected."
    message = (
        f"Transaction of ₹{transaction.amount:,.2f} to {transaction.receiver_name} ({transaction.receiver_id}) "
        f"triggered a risk score of {risk_score:.1f}/100."
    )

    alert = Alert(
        transaction_id=transaction.transaction_id,
        user_id=user.id,
        risk_level=risk_level,
        severity=severity,
        title=title,
        message=message,
        reason=reason_str,
        alert_status='ACTIVE'
    )
    db.session.add(alert)
    db.session.commit()
    return alert
