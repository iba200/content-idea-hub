# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

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

    return app
