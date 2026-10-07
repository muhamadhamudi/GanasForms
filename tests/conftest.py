import pytest
from app import create_app
from config import Config
from app.extensions import db
from app.models import User

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        u = User(username="admin", email="admin@example.com")
        u.set_password("password")
        db.session.add(u); db.session.commit()
    yield app
    with app.app_context(): db.session.remove(); db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()
