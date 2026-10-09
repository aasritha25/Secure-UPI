"""
Input validation utilities for API payloads.
"""

import re
from typing import Dict, List, Tuple


def validate_registration_payload(data: Dict) -> Tuple[bool, str]:
    if not data:
        return False, "Request body cannot be empty."

    required = ['name', 'email', 'phone', 'password']
    for field in required:
        if not data.get(field):
            return False, f"Field '{field}' is required."

    email = str(data.get('email')).strip()
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        return False, "Invalid email address format."

    phone = str(data.get('phone')).strip()
    if len(phone) < 10 or not re.match(r'^[0-9+ -]+$', phone):
        return False, "Invalid phone number format."

    password = str(data.get('password'))
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    return True, ""


def validate_transaction_payload(data: Dict) -> Tuple[bool, str]:
    if not data:
        return False, "Transaction payload cannot be empty."

    required = ['receiver_id', 'amount']
    for field in required:
        if field not in data or data.get(field) in (None, ''):
            return False, f"Field '{field}' is required."

    try:
        amount = float(data['amount'])
        if amount <= 0:
            return False, "Transaction amount must be strictly greater than zero."
        if amount > 1000000:
            return False, "Transaction amount exceeds single UPI transaction system limit of ₹10,00,000."
    except (ValueError, TypeError):
        return False, "Transaction amount must be a valid numerical value."

    receiver_id = str(data['receiver_id']).strip()
    if len(receiver_id) < 3:
        return False, "Receiver UPI ID or phone number is too short."

    return True, ""
