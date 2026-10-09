"""
Main Application Factory for Secure UPI: Machine Learning-Driven Fraud Detection System.
"""

import os
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from backend.config import Config
from backend.database.seeder import seed_database
from backend.extensions import cors, db, jwt
from backend.models import User
from backend.routes import (
    admin_bp,
    alerts_bp,
    auth_bp,
    dashboard_bp,
    model_metrics_bp,
    predict_bp,
    transactions_bp,
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')


def create_app(config_class=Config):
    app = Flask(
        __name__,
        static_folder=FRONTEND_DIR,
        template_folder=FRONTEND_DIR,
        static_url_path=''
    )
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # JWT Callbacks
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return user.id if isinstance(user, User) else str(user)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data['sub']
        return db.session.get(User, int(identity))

    # Register API Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(model_metrics_bp)

    # Database Initialization & Auto-Seeding
    with app.app_context():
        try:
            db.create_all()
            seed_database()
        except Exception as e:
            print(f"Warning during database initialization: {e}")

    # Health & System Status Endpoint
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'application': 'Secure UPI: Machine Learning-Driven Fraud Detection System',
            'version': '2.0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'ml_engine': 'operational'
        })

    # Serve Frontend Single-Page and Multi-Page Views
    @app.route('/')
    def index():
        return send_from_directory(FRONTEND_DIR, 'index.html')

    @app.route('/login')
    def login_page():
        return send_from_directory(FRONTEND_DIR, 'login.html')

    @app.route('/register')
    def register_page():
        return send_from_directory(FRONTEND_DIR, 'register.html')

    @app.route('/dashboard')
    def dashboard_page():
        return send_from_directory(FRONTEND_DIR, 'dashboard.html')

    @app.route('/transaction')
    def transaction_page():
        return send_from_directory(FRONTEND_DIR, 'transaction.html')

    @app.route('/alerts')
    def alerts_page():
        return send_from_directory(FRONTEND_DIR, 'alerts.html')

    @app.route('/profile')
    def profile_page():
        return send_from_directory(FRONTEND_DIR, 'profile.html')

    @app.route('/admin')
    def admin_page():
        return send_from_directory(FRONTEND_DIR, 'admin.html')

    @app.route('/fraud-analysis')
    def fraud_analysis_page():
        return send_from_directory(FRONTEND_DIR, 'fraud-analysis.html')

    # Serve static assets (CSS, JS, Fonts, Images)
    @app.route('/css/<path:filename>')
    def serve_css(filename):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'css'), filename)

    @app.route('/js/<path:filename>')
    def serve_js(filename):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'js'), filename)

    # General Static Fallback Handler
    @app.route('/<path:filename>')
    def serve_static(filename):
        # Don't intercept API routes
        if filename.startswith('api/') or filename.startswith('api'):
            return jsonify({'error': 'Resource not found', 'status_code': 404}), 404

        # Check exact filename (e.g. css/styles.css, js/config.js)
        file_path = os.path.join(FRONTEND_DIR, filename)
        if os.path.isfile(file_path):
            return send_from_directory(FRONTEND_DIR, filename)

        # Check filename with .html extension (e.g. /login -> login.html, /register -> register.html)
        html_path = file_path + '.html'
        if os.path.isfile(html_path):
            return send_from_directory(FRONTEND_DIR, filename + '.html')

        return send_from_directory(FRONTEND_DIR, 'index.html')

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found', 'status_code': 404}), 404
        return send_from_directory(FRONTEND_DIR, 'index.html'), 200

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error occurred', 'status_code': 500}), 500

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    print(f"Starting Secure UPI Full-Stack Platform on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
