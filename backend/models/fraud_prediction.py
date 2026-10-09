"""
FraudPrediction model for storing ML inferences and explainability data.
"""

import json
from datetime import datetime
from backend.extensions import db


class FraudPrediction(db.Model):
    __tablename__ = 'fraud_predictions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(80), db.ForeignKey('transactions.transaction_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    model_name = db.Column(db.String(60), nullable=False)
    fraud_probability = db.Column(db.Float, nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    prediction = db.Column(db.String(50), nullable=False)
    explanation = db.Column(db.Text, default='[]')
    feature_contributions = db.Column(db.Text, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='predictions')
    transaction = db.relationship('Transaction', back_populates='prediction_record')

    def to_dict(self):
        try:
            reasons = json.loads(self.explanation) if self.explanation else []
        except Exception:
            reasons = [self.explanation] if self.explanation else []

        try:
            contributions = json.loads(self.feature_contributions) if self.feature_contributions else []
        except Exception:
            contributions = []

        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'model_name': self.model_name,
            'fraud_probability': round(float(self.fraud_probability), 4),
            'risk_score': round(float(self.risk_score), 2),
            'risk_level': self.risk_level,
            'prediction': self.prediction,
            'reasons': reasons,
            'feature_contributions': contributions,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
