# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_mail import Mail
from config import Config
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()

# Limiter global
limiter = Limiter(key_func=get_remote_address)


def create_app(config_class=Config):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    # Disable CSRF in tests (detect via config or pytest env)
    if app.config.get('TESTING') or os.environ.get('PYTEST_CURRENT_TEST'):
        app.config['WTF_CSRF_ENABLED'] = False
    csrf.init_app(app)
    limiter.init_app(app)

    # Security headers via Talisman
    csp = app.config.get('CONTENT_SECURITY_POLICY')
    talisman = Talisman(
        app,
        content_security_policy=csp,
        force_https=app.config.get('FORCE_HTTPS', False),
        session_cookie_secure=app.config.get('SESSION_COOKIE_SECURE', False)
    )

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    login_manager.login_view = 'main.login'

    from app import routes, models, forms
    from app.routes import bp
    from app.admin_routes import admin_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(bp)

    # 👉 Injecter les settings dans tous les templates
    from app.utils.settings_manager import get_setting, DEFAULT_SETTINGS

    @app.context_processor
    def inject_settings():
        settings = {key: get_setting(key, default) for key, default in DEFAULT_SETTINGS.items()}
        return dict(settings=settings)

    # Expose CSRF token via cookie for JS fetch requests
    @app.after_request
    def set_csrf_cookie(response):
        if app.config.get('WTF_CSRF_ENABLED', True):
            csrf_token = generate_csrf()
            response.set_cookie(
                'XSRF-TOKEN',
                csrf_token,
                secure=app.config.get('SESSION_COOKIE_SECURE', False),
                httponly=False,
                samesite=app.config.get('SESSION_COOKIE_SAMESITE', 'Lax')
            )
        return response

    # Logging configuration (file + console)
    log_level = logging.INFO
    app.logger.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')

    # Rotating file handler
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(os.path.join(log_dir, 'app.log'), maxBytes=1_000_000, backupCount=3)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        app.logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    if not any(isinstance(h, logging.StreamHandler) for h in app.logger.handlers):
        app.logger.addHandler(console_handler)

    return app
