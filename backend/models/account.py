"""
Account model for Secure UPI balance and wallet simulation.
"""

from datetime import datetime
from backend.extensions import db


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    account_number_masked = db.Column(db.String(30), nullable=False)
    balance = db.Column(db.Float, default=100000.0, nullable=False)
    currency = db.Column(db.String(10), default='INR', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='account')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_number_masked': self.account_number_masked,
            'balance': round(float(self.balance), 2),
            'currency': self.currency,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
