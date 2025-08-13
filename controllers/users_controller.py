from main import db
from models import User

def get_all_users():
    return User.query.all()

def create_user(name, email, password):
    if User.query.filter_by(email=email).first():
        return None, "Email already exists"
    user = User(name=name, email=email)
    user.password = password  # hashes automatically
    db.session.add(user)
    db.session.commit()
    return user, None

def get_user(user_id):
    return User.query.get(user_id)

def update_user(user, name, email, password=None):
    user.name = name
    user.email = email
    if password:
        user.password = password
    db.session.commit()

def delete_user(user):
    db.session.delete(user)
    db.session.commit()
