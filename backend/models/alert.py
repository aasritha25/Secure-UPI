"""
Alert model for high-risk / suspicious transaction notifications.
"""

from datetime import datetime
from backend.extensions import db


class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(80), db.ForeignKey('transactions.transaction_id', ondelete='CASCADE'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    risk_level = db.Column(db.String(20), default='MEDIUM_RISK', nullable=False)
    severity = db.Column(db.String(20), default='MEDIUM', nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    title = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    reason = db.Column(db.Text, default='')
    alert_status = db.Column(db.String(30), default='ACTIVE', nullable=False) # ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='alerts')
    transaction = db.relationship('Transaction', back_populates='alert_record')

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else f"User #{self.user_id}",
            'user_email': self.user.email if self.user else None,
            'amount': self.transaction.amount if self.transaction else None,
            'risk_score': self.transaction.risk_score if self.transaction else None,
            'fraud_probability': self.transaction.fraud_probability if self.transaction else None,
            'risk_level': self.risk_level,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'reason': self.reason,
            'alert_status': self.alert_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
