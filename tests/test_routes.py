import pytest
from app import create_app, db
from app.models import User


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_register(client):
    response = client.post('/register', data={'username': 'testuser', 'password': 'testpass'})
    assert response.status_code == 302  # Redirect to login
    assert User.query.filter_by(username='testuser').first() is not None

def test_login(client):
    user = User(username='testuser')
    user.set_password('testpass')
    db.session.add(user)
    db.session.commit()
    response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    assert response.status_code == 302  # Redirect to index