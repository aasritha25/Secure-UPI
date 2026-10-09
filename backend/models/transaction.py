"""
Transaction model for UPI payments and simulation.
"""

import uuid
from datetime import datetime
from backend.extensions import db


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(80), unique=True, default=lambda: f"TXN-{uuid.uuid4().hex[:10].upper()}", nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    receiver_id = db.Column(db.String(80), nullable=False)
    receiver_name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    location = db.Column(db.String(80), default='Unknown')
    device_id = db.Column(db.String(80), default='Unknown')
    ip_address = db.Column(db.String(45), default='127.0.0.1')
    transaction_type = db.Column(db.String(40), default='P2P') # P2P, P2M, BILL_PAYMENT, ONLINE_SHOPPING, INVESTMENT, RECHARGE
    status = db.Column(db.String(30), default='SUCCESS', nullable=False) # SUCCESS, FLAGGED, BLOCKED, FAILED
    risk_score = db.Column(db.Float, default=0.0) # 0 to 100
    risk_level = db.Column(db.String(20), default='LOW_RISK') # LOW_RISK, MEDIUM_RISK, HIGH_RISK
    fraud_probability = db.Column(db.Float, default=0.0)
    prediction = db.Column(db.String(50), default='Legitimate') # Legitimate, Suspicious, Fraudulent
    note = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='transactions')
    prediction_record = db.relationship('FraudPrediction', uselist=False, back_populates='transaction', cascade='all, delete-orphan')
    alert_record = db.relationship('Alert', uselist=False, back_populates='transaction', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else f"User #{self.user_id}",
            'user_email': self.user.email if self.user else None,
            'receiver_id': self.receiver_id,
            'receiver_name': self.receiver_name,
            'amount': round(float(self.amount), 2),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'location': self.location,
            'device_id': self.device_id,
            'ip_address': self.ip_address,
            'transaction_type': self.transaction_type,
            'status': self.status,
            'risk_score': round(float(self.risk_score), 2),
            'risk_level': self.risk_level,
            'fraud_probability': round(float(self.fraud_probability), 4),
            'prediction': self.prediction,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
