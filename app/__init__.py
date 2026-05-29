from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Расширения Flask создаются один раз и инициализируются внутри фабрики приложения.
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Войдите в систему для продолжения работы.'


def create_app(test_config=None):
    """Фабрика приложения StudentRequest.

    test_config используется в автоматических тестах и позволяет подменять БД,
    SECRET_KEY и другие параметры без изменения основного кода проекта.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev-secret-key-change-before-deploy',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + str(Path(app.instance_path) / 'student_request.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=str(Path(app.root_path) / 'static' / 'uploads'),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

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
