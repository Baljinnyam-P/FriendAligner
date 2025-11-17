from ..models import User
from ..extensions import db

# Service function to create a new user
def create_user(email, password, first_name=None, last_name=None, phone=None):
    user = User(email=email, first_name=first_name, last_name=last_name, phone_number=phone)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user
