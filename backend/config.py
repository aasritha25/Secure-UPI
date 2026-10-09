"""
Application Configuration for Secure UPI Full-Stack Platform.
Supports environment variables for production security with fallback to local SQLite.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'secure-upi-secret-key-2026-ml-fintech')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-super-secret-key-secure-upi-auth')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_EXPIRES_HOURS', 12)))

    # Database Configuration (Defaults to local SQLite, easily switches to MySQL or PostgreSQL)
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Check if running in a read-only environment or serverless runtime
        is_serverless = bool(
            os.getenv('VERCEL') or 
            os.getenv('VERCEL_ENV') or 
            os.getenv('AWS_LAMBDA_FUNCTION_NAME') or 
            not os.access(BASE_DIR, os.W_OK)
        )
        if is_serverless:
            DB_PATH = '/tmp/secure_upi.db'
        else:
            DB_PATH = os.path.join(BASE_DIR, 'secure_upi.db')
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Configurable Fraud Detection Thresholds (Academic FinTech demonstration)
    LOW_RISK_MAX = float(os.getenv('LOW_RISK_MAX', 30.0))
    MEDIUM_RISK_MAX = float(os.getenv('MEDIUM_RISK_MAX', 70.0))
    HIGH_RISK_MIN = float(os.getenv('HIGH_RISK_MIN', 71.0))
