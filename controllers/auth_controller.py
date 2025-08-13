from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user
from models import User  # your SQLAlchemy User model
from main import app
from functools import wraps
from flask import abort
from sqlalchemy.orm import joinedload

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_get"

@login_manager.user_loader
def load_user(user_id):
    return User.query.options(
        joinedload(User.admin),
        joinedload(User.worker)
    ).filter_by(id=int(user_id)).first()

def authenticate(email, password):
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        return user
    return None

def login(user):
    login_user(user)

def logout():
    logout_user()

def is_logged_in():
    return current_user.is_authenticated

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized

            has_role = False

            if "admin" in roles and hasattr(current_user, "admin") and current_user.admin is not None:
                has_role = True

            if "secretary" in roles:
                # Check if user has a worker and that worker's role is secretary
                if hasattr(current_user, "worker") and current_user.worker is not None:
                    # Adjust the attribute name for the worker's role field here
                    if current_user.worker.secretary is not None:
                        has_role = True

            if not has_role:
                abort(403)  # Forbidden

            return f(*args, **kwargs)
        return decorated_function
    return decorator
