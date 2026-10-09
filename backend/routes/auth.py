"""
Authentication routes for Secure UPI.
Handles user registration, login, JWT token issuance, and profile retrieval.
"""

from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from backend.extensions import db
from backend.models import Account, LoginHistory, User, UserDevice
from backend.utils.validators import validate_registration_payload

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    payload = request.get_json(silent=True) or {}
    is_valid, err_msg = validate_registration_payload(payload)
    if not is_valid:
        return jsonify({'error': err_msg}), 400

    email = str(payload['email']).strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'An account with this email already exists.'}), 400

    phone = str(payload['phone']).strip()
    name = str(payload['name']).strip()
    role = str(payload.get('role', 'customer')).lower()
    if role not in ('customer', 'admin'):
        role = 'customer'

    user = User(
        name=name,
        email=email,
        phone=phone,
        role=role,
        language=str(payload.get('language', 'en'))
    )
    user.password = payload['password']
    db.session.add(user)
    db.session.flush()

    # Create account with initial balance
    initial_balance = float(payload.get('initial_balance', 100000.0))
    account = Account(
        user_id=user.id,
        account_number_masked=f"**** {str(user.id).zfill(4)}",
        balance=max(0.0, initial_balance),
        currency='INR'
    )
    db.session.add(account)

    # Register initial device
    device_id = str(payload.get('device_id', 'DEV_WEB_CHROME'))
    device = UserDevice(
        user_id=user.id,
        device_id=device_id,
        device_name=str(payload.get('device_name', 'Web Browser')),
        ip_address=request.remote_addr or '127.0.0.1',
        location=str(payload.get('location', 'Hyderabad')),
        is_trusted=True
    )
    db.session.add(device)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({
        'message': 'User registration successful.',
        'access_token': token,
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get('email', '')).strip().lower()
    password = str(payload.get('password', ''))

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email credentials or password.'}), 401

    # Record login
    login_entry = LoginHistory(
        user_id=user.id,
        ip_address=request.remote_addr or '127.0.0.1',
        device_id=str(payload.get('device_id', 'DEV_DEFAULT')),
        location=str(payload.get('location', 'Hyderabad')),
        status='SUCCESS'
    )
    db.session.add(login_entry)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({
        'message': 'Login successful.',
        'access_token': token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    return jsonify({'user': user.to_dict()})


@auth_bp.route('/profile', methods=['GET', 'PUT'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    if request.method == 'PUT':
        payload = request.get_json(silent=True) or {}
        if 'name' in payload:
            user.name = str(payload['name']).strip()
        if 'phone' in payload:
            user.phone = str(payload['phone']).strip()
        if 'language' in payload:
            user.language = str(payload['language']).strip()
        if 'balance' in payload and user.account:
            try:
                user.account.balance = max(0.0, float(payload['balance']))
                user.account.updated_at = datetime.utcnow()
            except (ValueError, TypeError):
                pass
        db.session.commit()

    # Generate UPI ID / VPA from phone number or name
    upi_vpa = f"{user.phone}@secureupi" if user.phone else f"{user.id}@secureupi"

    return jsonify({
        'user': user.to_dict(),
        'account': user.account.to_dict() if user.account else None,
        'upi_vpa': upi_vpa,
        'linked_bank': {
            'bank_name': 'State Bank of India / HDFC Bank (Simulated Primary)',
            'account_number_masked': user.account.account_number_masked if user.account else '**** 4829',
            'ifsc': 'SBIN0001234',
            'account_type': 'Savings Account'
        },
        'secondary_bank': {
            'bank_name': 'ICICI Bank (Simulated Secondary Account)',
            'account_number_masked': '**** 8892',
            'ifsc': 'ICIC0005678',
            'account_type': 'Salary / Current Account'
        },
        'wallet': {
            'wallet_id': f"WAL-{user.id:04d}",
            'balance': user.account.balance if user.account else 0.0,
            'status': 'ACTIVE'
        }
    })


@auth_bp.route('/balance', methods=['POST', 'PUT'])
@jwt_required()
def update_balance():
    """
    Allows user to change/customize their balance dynamically to any desired amount.
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user or not user.account:
        return jsonify({'error': 'User account not found.'}), 404

    payload = request.get_json(silent=True) or {}
    if 'balance' not in payload and 'amount' not in payload:
        return jsonify({'error': 'Please provide a valid balance amount.'}), 400

    try:
        new_balance = float(payload.get('balance', payload.get('amount', 0)))
        if new_balance < 0:
            return jsonify({'error': 'Balance amount cannot be negative.'}), 400
        if new_balance > 10000000:
            return jsonify({'error': 'Balance exceeds maximum limit of ₹1,00,00,000.'}), 400
            
        user.account.balance = round(new_balance, 2)
        user.account.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Account balance updated successfully.',
            'new_balance': user.account.balance,
            'currency': user.account.currency,
            'updated_at': user.account.updated_at.isoformat()
        }), 200
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid numerical value for balance.'}), 400


@auth_bp.route('/check-balance', methods=['POST'])
@jwt_required()
def check_balance():
    """
    Simulates real UPI Check Balance flow with 4/6-digit UPI PIN verification.
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user or not user.account:
        return jsonify({'error': 'User account not found.'}), 404

    payload = request.get_json(silent=True) or {}
    pin = str(payload.get('upi_pin', '')).strip()

    # For simulation, validate that a 4 or 6 digit PIN is entered
    if not pin or len(pin) not in (4, 6) or not pin.isdigit():
        return jsonify({'error': 'Please enter a valid 4 or 6 digit UPI PIN.'}), 400

    return jsonify({
        'status': 'SUCCESS',
        'message': 'UPI PIN verified successfully.',
        'bank_name': 'State Bank of India (Simulated)',
        'account_number_masked': user.account.account_number_masked,
        'available_balance': user.account.balance,
        'currency': 'INR',
        'account_type': 'Savings Account',
        'upi_vpa': f"{user.phone}@secureupi",
        'checked_at': datetime.utcnow().isoformat()
    }), 200
