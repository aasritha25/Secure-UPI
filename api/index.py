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
    """
    Normalizes WSGI SCRIPT_NAME and PATH_INFO when Vercel routes requests to api/index.py.
    Preserves frontend HTML page routes (/alerts, /dashboard, etc.) while prefixing API calls.
    """

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        script_name = environ.get('SCRIPT_NAME', '')
        path_info = environ.get('PATH_INFO', '')
        raw_path = script_name + path_info

        # Strip Vercel serverless script prefix if present
        if raw_path.startswith('/api/index.py'):
            raw_path = raw_path[len('/api/index.py'):] or '/'
        elif raw_path.startswith('/api/index'):
            raw_path = raw_path[len('/api/index'):] or '/'

        # List of frontend page & static asset routes that must NOT be prefixed with /api
        frontend_pages = (
            '/', '/login', '/register', '/dashboard', '/transaction', 
            '/alerts', '/profile', '/admin', '/fraud-analysis'
        )

        # Preserve frontend HTML pages and static assets
        if raw_path in frontend_pages or raw_path.startswith('/css/') or raw_path.startswith('/js/'):
            pass
        elif not raw_path.startswith('/api/'):
            raw_path = '/api' + ('' if raw_path.startswith('/') else '/') + raw_path

        environ['SCRIPT_NAME'] = ''
        environ['PATH_INFO'] = raw_path

        return self.wsgi_app(environ, start_response)


# Wrap Flask WSGI app with Vercel path normalizer
app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)

# Vercel entry points
app = app
handler = app
