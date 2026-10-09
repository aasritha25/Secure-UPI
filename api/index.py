"""
Vercel Serverless Entrypoint for Secure UPI: Machine Learning Fraud Detection System
"""

import os
import sys

# Add project root to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import app

# Vercel WSGI entry point
# Exports the Flask app instance
app = app
