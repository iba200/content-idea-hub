
"""
Flask application factory.

Returns:
    Flask: The Flask application instance.
"""
from math import e
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config



db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_class=Config):
    """Create a Flask application instance.

    Args:
        config_class (Config, optional):
        The configuration class to use. Defaults to Config.

    Returns:
        Flask: The Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User  # Import local pour éviter circular
        return User.query.get(int(user_id))
    
    login_manager.login_view = 'main.login'

    from app import routes, models, forms
    from app.routes import bp
    
    app.register_blueprint(bp)
    return app
