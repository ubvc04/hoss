import os
from flask import Flask, jsonify
from flask_cors import CORS
from .config import Config
from .database import init_db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS
    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}},
         supports_credentials=True)

    # Ensure upload directory exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    # Initialize DB
    is_new = init_db()

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.users import users_bp
    from .routes.patients import patients_bp
    from .routes.visits import visits_bp
    from .routes.clinical import clinical_bp
    from .routes.prescriptions import prescriptions_bp
    from .routes.reports import reports_bp
    from .routes.appointments import appointments_bp
    from .routes.billing import billing_bp
    from .routes.notifications import notifications_bp
    from .routes.audit import audit_bp
    from .routes.dashboard import dashboard_bp
    from .routes.blockchain import blockchain_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(visits_bp)
    app.register_blueprint(clinical_bp)
    app.register_blueprint(prescriptions_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(blockchain_bp, url_prefix='/api/blockchain')

    # Seed data on first run
    if is_new:
        with app.app_context():
            from .seed import seed_data
            seed_data()

    # Global error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request'}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Method not allowed'}), 405

    @app.errorhandler(413)
    def payload_too_large(e):
        return jsonify({'error': 'File too large. Maximum 50MB allowed.'}), 413

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Internal server error'}), 500

    # Health check
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'service': 'Hospital Management System API'}), 200

    return app
