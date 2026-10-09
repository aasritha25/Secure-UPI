from __future__ import annotations

import uuid
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from backend.extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default='customer', nullable=False)
    language = db.Column(db.String(20), default='en', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship('Account', uselist=False, back_populates='user', cascade='all, delete-orphan')
    transactions = db.relationship('PaymentTransaction', back_populates='user', cascade='all, delete-orphan')
    analyses = db.relationship('FraudAnalysis', back_populates='user', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', back_populates='user', cascade='all, delete-orphan')

    @property
    def password(self):
        raise AttributeError('Password is not readable')

    @password.setter
    def password(self, value):
        self.password_hash = generate_password_hash(value)

    def verify_password(self, value):
        return check_password_hash(self.password_hash, value)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'language': self.language,
            'account_balance': self.account.balance if self.account else 0,
        }


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    account_number_masked = db.Column(db.String(30), nullable=False)
    balance = db.Column(db.Float, default=100000.0, nullable=False)
    currency = db.Column(db.String(10), default='INR', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='account')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_number_masked': self.account_number_masked,
            'balance': self.balance,
            'currency': self.currency,
        }


class PaymentTransaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(80), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.String(80), nullable=False)
    receiver_name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text, default='')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(80), default='Unknown')
    device_id = db.Column(db.String(80), default='Unknown')
    status = db.Column(db.String(30), default='DRAFT', nullable=False)
    risk_percentage = db.Column(db.Float, default=0.0)
    risk_level = db.Column(db.String(20), default='LOW_RISK')
    fraud_probability = db.Column(db.Float, default=0.0)
    prediction = db.Column(db.String(50), default='SAFE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='transactions')

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'receiver_id': self.receiver_id,
            'receiver_name': self.receiver_name,
            'amount': self.amount,
            'note': self.note,
            'location': self.location,
            'device_id': self.device_id,
            'status': self.status,
            'risk_percentage': self.risk_percentage,
            'risk_level': self.risk_level,
            'fraud_probability': self.fraud_probability,
            'prediction': self.prediction,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


class FraudAnalysis(db.Model):
    __tablename__ = 'fraud_predictions'

    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.String(80), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.String(80), nullable=False)
    receiver_name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(80), default='Unknown')
    device_id = db.Column(db.String(80), default='Unknown')
    transaction_frequency = db.Column(db.Float, default=0.0)
    average_amount = db.Column(db.Float, default=0.0)
    time_since_last_transaction = db.Column(db.Float, default=0.0)
    fraud_probability = db.Column(db.Float, default=0.0)
    risk_percentage = db.Column(db.Float, default=0.0)
    risk_level = db.Column(db.String(20), default='LOW_RISK')
    prediction = db.Column(db.String(50), default='SAFE')
    recommendation = db.Column(db.String(120), default='CONTINUE')
    reasons = db.Column(db.Text, default='[]')
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='analyses')

    def to_dict(self):
        return {
            'analysis_id': self.analysis_id,
            'receiver_name': self.receiver_name,
            'receiver_id': self.receiver_id,
            'amount': self.amount,
            'location': self.location,
            'device_id': self.device_id,
            'fraud_probability': self.fraud_probability,
            'risk_percentage': self.risk_percentage,
            'risk_level': self.risk_level,
            'prediction': self.prediction,
            'recommendation': self.recommendation,
            'reasons': self.reasons,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    alert_type = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='INFO')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='alerts')

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.alert_type,
            'title': self.title,
            'message': self.message,
            'severity': self.severity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


def seed_demo_data():
    if User.query.filter_by(email='demo@secureupi.com').first():
        return

    admin = User(
        name='Secure Admin',
        email='admin@secureupi.com',
        phone='9999999999',
        password='admin123',
        role='admin',
        language='en'
    )
    user = User(
        name='Aarav Sharma',
        email='demo@secureupi.com',
        phone='9876543210',
        password='demo123',
        role='customer',
        language='en'
    )
    db.session.add_all([admin, user])
    db.session.flush()

    account = Account(
        user_id=user.id,
        account_number_masked='**** 6543',
        balance=100000.0,
        currency='INR'
    )
    db.session.add(account)

    admin_account = Account(
        user_id=admin.id,
        account_number_masked='**** 1111',
        balance=1000000.0,
        currency='INR'
    )
    db.session.add(admin_account)

    transactions = [
        PaymentTransaction(
            user_id=user.id,
            receiver_id='coffeehouse',
            receiver_name='Café House',
            amount=650.0,
            note='Breakfast payment',
            location='Hyderabad',
            device_id='device-01',
            status='SUCCESS',
            risk_percentage=12,
            risk_level='LOW_RISK',
            fraud_probability=0.12,
            prediction='SAFE',
            timestamp=datetime.utcnow()
        ),
        PaymentTransaction(
            user_id=user.id,
            receiver_id='bookmart',
            receiver_name='Book Mart',
            amount=2800.0,
            note='Study supplies',
            location='Hyderabad',
            device_id='device-01',
            status='SUCCESS',
            risk_percentage=16,
            risk_level='LOW_RISK',
            fraud_probability=0.16,
            prediction='SAFE',
            timestamp=datetime.utcnow()
        ),
        PaymentTransaction(
            user_id=user.id,
            receiver_id='electronics',
            receiver_name='Urban Electronics',
            amount=18000.0,
            note='Portable speaker',
            location='Bengaluru',
            device_id='device-02',
            status='SUCCESS',
            risk_percentage=39,
            risk_level='MEDIUM_RISK',
            fraud_probability=0.39,
            prediction='SUSPICIOUS',
            timestamp=datetime.utcnow()
        ),
    ]
    db.session.add_all(transactions)

    alerts = [
        Alert(
            user_id=user.id,
            alert_type='security',
            title='Device verification needed',
            message='A recent payment came from a new device at a changed location.',
            severity='MEDIUM'
        ),
        Alert(
            user_id=user.id,
            alert_type='fraud',
            title='Weekly risk summary',
            message='Your transaction behavior remains within safe operating limits.',
            severity='LOW'
        )
    ]
    db.session.add_all(alerts)
    db.session.commit()
