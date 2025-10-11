import os

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
login_manager = LoginManager()
jwt = JWTManager()


def create_app(config_object=None):
    app = Flask(__name__)

    db_uri = os.environ.get("DATABASE_URL")
    if not db_uri:
        db_uri = "sqlite:///employees.db"

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret"),
        SEED_DEFAULT_DATA=(os.environ.get("SEED_DEFAULT_DATA", "true").lower() in {"1", "true", "yes"}),
    )

    if config_object:
        if isinstance(config_object, str):
            app.config.from_object(config_object)
        else:
            app.config.from_mapping(config_object)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    jwt.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .auth import auth_bp, api_auth_bp
    from .routes import main_bp
    from .api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        if app.config.get("TESTING"):
            db.create_all()
            if app.config.get("SEED_DEFAULT_DATA", True):
                from .seed import seed_defaults

                seed_defaults()

    return app


app = create_app()
