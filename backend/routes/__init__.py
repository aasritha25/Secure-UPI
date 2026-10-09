"""
Routes Package Initialization.
"""

from backend.routes.auth import auth_bp
from backend.routes.transactions import transactions_bp
from backend.routes.predict import predict_bp
from backend.routes.alerts import alerts_bp
from backend.routes.dashboard import dashboard_bp
from backend.routes.admin import admin_bp
from backend.routes.model_metrics import model_metrics_bp

__all__ = [
    'auth_bp',
    'transactions_bp',
    'predict_bp',
    'alerts_bp',
    'dashboard_bp',
    'admin_bp',
    'model_metrics_bp'
]
