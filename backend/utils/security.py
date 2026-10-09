"""
Security utilities and RBAC (Role-Based Access Control) decorators.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from backend.extensions import db
from backend.models import User


def admin_required():
    """
    Decorator to restrict API access to users with 'admin' role.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = db.session.get(User, int(user_id))
            if not user or user.role != 'admin':
                return jsonify({
                    'error': 'Forbidden: Administrator privileges required for this resource.',
                    'status_code': 403
                }), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def customer_required():
    """
    Decorator to restrict API access to authenticated users.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = db.session.get(User, int(user_id))
            if not user:
                return jsonify({
                    'error': 'Unauthorized: User account not found.',
                    'status_code': 401
                }), 401
            return fn(*args, **kwargs)
        return decorator
    return wrapper
