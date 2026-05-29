from app import create_app, db
from app.models import User


def test_app_factory_creates_app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    assert app is not None
    assert app.config['TESTING'] is True


def test_database_initialization():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        user = User(full_name='Тестовый пользователь', email='test@example.com', role='student', password_hash='hash')
        db.session.add(user)
        db.session.commit()
        assert User.query.count() == 1
