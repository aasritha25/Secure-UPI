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


class VercelWSGIMiddleware:

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        script_name = environ.get('SCRIPT_NAME', '')
        path_info = environ.get('PATH_INFO', '')

        # When Vercel rewrites /api/* to /api/index.py, SCRIPT_NAME may be '/api' and PATH_INFO '/auth/login'
        # Combine them so Flask receives '/api/auth/login' as expected by blueprints.
        if script_name:
            full_path = script_name + path_info
            environ['SCRIPT_NAME'] = ''
            environ['PATH_INFO'] = full_path

        return self.wsgi_app(environ, start_response)


# Wrap Flask WSGI app with Vercel path normalizer
app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
handler = app

