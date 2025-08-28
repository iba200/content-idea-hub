import pytest
from app import create_app, db
from app.models import User, Idea

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
    with client.application.app_context():
        assert User.query.filter_by(username='testuser').first() is not None

def test_login(client):
    with client.application.app_context():
        user = User(username='testuser')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
    response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    assert response.status_code == 302  # Redirect to indeximport pytest
from app import create_app, db
from app.models import User, Idea

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
    with client.application.app_context():
        assert User.query.filter_by(username='testuser').first() is not None

def test_login(client):
    with client.application.app_context():
        user = User(username='testuser')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
    response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    assert response.status_code == 302  # Redirect to index

def test_new_idea(client):
    with client.application.app_context():
        user = User(username='testuser')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    response = client.post('/idea/new', data={'title': 'Test Idea', 'description': 'Desc', 'tags': 'test,fun', 'status': 'Draft'})
    assert response.status_code == 302  # Redirect to index
    with client.application.app_context():
        assert Idea.query.filter_by(title='Test Idea').first() is not None