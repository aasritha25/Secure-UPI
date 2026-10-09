"""
Vercel Serverless Entrypoint for Secure UPI: Machine Learning Fraud Detection System
"""

import os
import sys

# Ensure project root is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import app

# Vercel WSGI entry points
app = app
handler = app
