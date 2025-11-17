import os
import sys
import uuid
import pytest

os.environ.setdefault("DATABASE_URI", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt")

# Fix package import error 
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.extensions import db
from app.models import User, Group, GroupMember, Event, ChatMessage, Notification

@pytest.fixture(scope="function")
def app():
    #Provide a fresh app + in-memory DB per test for isolation.
    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        yield flask_app
        db.session.remove()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def db_session(app):
    with app.app_context():
        yield db.session

@pytest.fixture()
def user_factory(db_session):
    def _create(email=None, password="pass", first_name="Test", last_name="User", is_admin=False):
        if email is None:
            email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        u = User(email=email, first_name=first_name, last_name=last_name, is_admin=is_admin)
        u.set_password(password)
        db_session.add(u)
        db_session.commit()
        return u
    return _create

@pytest.fixture()
def token_factory(client, user_factory):
    def _token(user=None):
        if user is None:
            user = user_factory()
        resp = client.post("/api/auth/login", json={"email": user.email, "password": "pass"})
        assert resp.status_code == 200
        return resp.get_json()["access_token"], user
    return _token

@pytest.fixture()
def group_factory(db_session, user_factory):
    def _group(owner=None, name="My Group"):
        if owner is None:
            owner = user_factory()  # unique email auto-generated
        g = Group(group_name=name, user_id=owner.user_id)
        db_session.add(g)
        db_session.commit()
        return g, owner
    return _group

@pytest.fixture()
def member_factory(db_session, user_factory):
    def _member(group, user=None, role="member"):
        if user is None:
            user = user_factory(email=f"member{group.group_id}@example.com")
        gm = GroupMember(group_id=group.group_id, user_id=user.user_id, role=role)
        db_session.add(gm)
        db_session.commit()
        return gm, user
    return _member
