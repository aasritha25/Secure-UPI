"""
Unit & Integration Test Suite for Secure UPI Fraud Detection System.
Tests:
- User registration & login
- JWT authentication & authorization
- Transaction creation & balance deductions
- ML Fraud prediction & Risk scoring
- Alert generation for high/medium risk transactions
- Dashboard statistics APIs
- Invalid inputs & Unauthorized access protection
"""

import json
import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models import User, Account, Transaction, Alert


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-jwt-secret-key-that-is-at-least-32-bytes-long-for-sha256'


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def get_auth_token(client, email='demo@secureupi.com', password='demo123'):
    res = client.post('/api/auth/login', json={'email': email, 'password': password})
    data = res.get_json()
    return data.get('access_token')


# ================= 1. Authentication Tests =================
def test_user_registration(client):
    res = client.post('/api/auth/register', json={
        'name': 'Test User',
        'email': 'testuser@example.com',
        'phone': '9876500000',
        'password': 'password123',
        'initial_balance': 50000
    })
    assert res.status_code == 201
    data = res.get_json()
    assert 'access_token' in data
    assert data['user']['email'] == 'testuser@example.com'
    assert data['user']['account_balance'] == 50000


def test_user_login_success(client):
    token = get_auth_token(client, 'demo@secureupi.com', 'demo123')
    assert token is not None


def test_user_login_invalid_password(client):
    res = client.post('/api/auth/login', json={
        'email': 'demo@secureupi.com',
        'password': 'wrongpassword'
    })
    assert res.status_code == 401
    assert 'Invalid email' in res.get_json()['error']


# ================= 2. JWT & Unauthorized Access Tests =================
def test_unauthorized_dashboard_access(client):
    res = client.get('/api/dashboard/stats')
    assert res.status_code == 401


def test_authorized_dashboard_access(client):
    token = get_auth_token(client)
    res = client.get('/api/dashboard/stats', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert 'metrics' in data
    assert 'available_balance' in data['metrics']


def test_admin_route_forbidden_for_customer(client):
    token = get_auth_token(client, 'demo@secureupi.com', 'demo123')
    res = client.get('/api/admin/stats', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 403


def test_admin_route_allowed_for_admin(client):
    admin_token = get_auth_token(client, 'admin@secureupi.com', 'admin123')
    res = client.get('/api/admin/stats', headers={'Authorization': f'Bearer {admin_token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert 'kpis' in data
    assert 'total_users' in data['kpis']


# ================= 3. ML Fraud Prediction & Risk Scoring Tests =================
def test_predict_legitimate_transaction(client):
    token = get_auth_token(client)
    res = client.post('/api/predict', json={
        'receiver_id': 'cafe@upi',
        'receiver_name': 'Cafe',
        'amount': 350.0,
        'average_amount': 1200.0,
        'location': 'Hyderabad',
        'device_id': 'DEV_ANDROID_14_HYD',
        'time_of_day': 14,
        'transaction_velocity': 1.0,
        'time_since_last_transaction': 180,
        'failed_transactions': 0
    }, headers={'Authorization': f'Bearer {token}'})

    assert res.status_code == 200
    data = res.get_json()
    assert 'risk_score' in data
    assert 'fraud_probability' in data
    assert data['risk_level'] == 'LOW_RISK'
    assert data['transaction_status'] == 'Legitimate'


def test_predict_high_risk_transaction(client):
    token = get_auth_token(client)
    res = client.post('/api/predict', json={
        'receiver_id': 'unverified.merchant88@ybl',
        'receiver_name': 'Unknown Node',
        'amount': 85000.0,
        'average_amount': 1000.0,
        'location': 'Kolkata',
        'device_id': 'DEV_UNKNOWN_EMULATOR',
        'time_of_day': 3,
        'transaction_velocity': 8.5,
        'time_since_last_transaction': 2,
        'failed_transactions': 4
    }, headers={'Authorization': f'Bearer {token}'})

    assert res.status_code == 200
    data = res.get_json()
    assert data['risk_score'] >= 70.0
    assert data['risk_level'] == 'HIGH_RISK'
    assert data['transaction_status'] == 'Fraudulent'
    assert len(data['reasons']) > 0


# ================= 4. Transaction Creation & Balance Tests =================
def test_create_legitimate_transaction_deducts_balance(client):
    token = get_auth_token(client)
    
    # Get initial balance
    dash_before = client.get('/api/dashboard/stats', headers={'Authorization': f'Bearer {token}'}).get_json()
    initial_balance = dash_before['metrics']['available_balance']

    # Execute transaction
    res = client.post('/api/transactions', json={
        'receiver_id': 'groceries@upi',
        'receiver_name': 'Grocery Store',
        'amount': 1500.0,
        'location': 'Hyderabad',
        'device_id': 'DEV_ANDROID_14_HYD'
    }, headers={'Authorization': f'Bearer {token}'})

    assert res.status_code == 201
    data = res.get_json()
    assert data['status'] == 'SUCCESS'
    assert data['remaining_balance'] == initial_balance - 1500.0


def test_create_high_risk_transaction_blocked_and_alert_generated(client):
    token = get_auth_token(client)

    res = client.post('/api/transactions', json={
        'receiver_id': 'crypto.drain@ybl',
        'receiver_name': 'Unknown Crypto Gateway',
        'amount': 95000.0,
        'average_amount': 1000.0,
        'location': 'Kolkata',
        'device_id': 'DEV_UNKNOWN_EMULATOR',
        'time_of_day': 3,
        'failed_transactions': 4,
        'transaction_velocity': 9.0,
        'time_since_last_transaction': 1
    }, headers={'Authorization': f'Bearer {token}'})

    assert res.status_code == 201
    data = res.get_json()
    assert data['status'] == 'BLOCKED'
    assert data['risk_level'] == 'HIGH_RISK'
    assert data['alert_created'] is True


# ================= 5. Validation & Edge Cases Tests =================
def test_transaction_invalid_negative_amount(client):
    token = get_auth_token(client)
    res = client.post('/api/transactions', json={
        'receiver_id': 'shop@upi',
        'amount': -500.0
    }, headers={'Authorization': f'Bearer {token}'})

    assert res.status_code == 400
    assert 'greater than zero' in res.get_json()['error']


def test_model_metrics_endpoint(client):
    res = client.get('/api/model/metrics')
    assert res.status_code == 200
    data = res.get_json()
    assert 'models' in data
    assert 'selected_model' in data
    assert 'Random Forest' in data['models']
    assert 'Logistic Regression' in data['models']
    assert 'XGBoost' in data['models']


# ================= 6. Custom Balance & Check Balance Tests =================
def test_custom_balance_update(client):
    token = get_auth_token(client)
    res = client.post('/api/auth/balance', json={
        'balance': 350000.0
    }, headers={'Authorization': f'Bearer {token}'})

    assert res.status_code == 200
    data = res.get_json()
    assert data['new_balance'] == 350000.0

    # Verify profile reflects the new balance
    prof_res = client.get('/api/auth/profile', headers={'Authorization': f'Bearer {token}'})
    assert prof_res.status_code == 200
    assert prof_res.get_json()['account']['balance'] == 350000.0


def test_check_balance_with_pin(client):
    token = get_auth_token(client)
    res = client.post('/api/auth/check-balance', json={
        'upi_pin': '1234'
    }, headers={'Authorization': f'Bearer {token}'})

    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'SUCCESS'
    assert 'available_balance' in data
    assert 'bank_name' in data
    assert 'account_number_masked' in data


def test_pay_through_mobile_and_self_transfer(client):
    token = get_auth_token(client)
    
    # 1. Pay to Mobile
    res_mob = client.post('/api/transactions', json={
        'receiver_id': '9812345678@secureupi',
        'receiver_name': 'Priya Patel',
        'amount': 850.0,
        'transaction_type': 'P2P'
    }, headers={'Authorization': f'Bearer {token}'})
    assert res_mob.status_code == 201
    assert res_mob.get_json()['status'] == 'SUCCESS'

    # 2. Self Bank Transfer
    res_self = client.post('/api/transactions', json={
        'receiver_id': 'self.icici@secureupi',
        'receiver_name': 'My ICICI Salary Account',
        'amount': 5000.0,
        'transaction_type': 'P2P'
    }, headers={'Authorization': f'Bearer {token}'})
    assert res_self.status_code == 201
    assert res_self.get_json()['status'] == 'SUCCESS'

