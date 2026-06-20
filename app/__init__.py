import os
from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Расширения создаются на уровне пакета и инициализируются в create_app.
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Войдите в систему для продолжения работы.'


def _database_uri_from_env() -> str:
    """Возвращает URI БД из переменной окружения с учетом Render/Heroku."""
    uri = os.getenv('DATABASE_URL', 'sqlite:///student_request.db')
    if uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql://', 1)
    return uri


def create_app(config_overrides: dict | None = None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'change-this-secret-key'),
        SQLALCHEMY_DATABASE_URI=_database_uri_from_env(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=str(Path(app.root_path) / 'static' / 'uploads'),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        WTF_CSRF_ENABLED=True,
        SLA_HOURS_LOW=72,
        SLA_HOURS_NORMAL=48,
        SLA_HOURS_HIGH=24,
        MAIL_NOTIFICATIONS_ENABLED=False,
    )
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .models import User
    from .security import get_csrf_token

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_security_helpers():
        return {'csrf_token': get_csrf_token}

    from .routes_auth import auth_bp
    from .routes_main import main_bp
    from .routes_student import student_bp
    from .routes_employee import employee_bp
    from .routes_admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(employee_bp, url_prefix='/employee')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    return app
