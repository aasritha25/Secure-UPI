"""
User model for Secure UPI.
"""

from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from backend.extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default='customer', nullable=False) # 'customer' or 'admin'
    language = db.Column(db.String(10), default='en', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    account = db.relationship('Account', uselist=False, back_populates='user', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    predictions = db.relationship('FraudPrediction', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    alerts = db.relationship('Alert', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    devices = db.relationship('UserDevice', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    login_history = db.relationship('LoginHistory', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('Password is not directly readable')

    @password.setter
    def password(self, plain_password):
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        return check_password_hash(self.password_hash, plain_password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'account_balance': self.account.balance if self.account else 0.0,
            'account_number_masked': self.account.account_number_masked if self.account else 'N/A'
        }
