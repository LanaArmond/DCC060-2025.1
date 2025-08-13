import os
from flask import Flask
from dotenv import load_dotenv
from models import db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)



from routes.main_routes import *
from routes.users_routes import users_bp
from routes.presentation_routes import presentations_bp
from routes.queries_routes import queries_bp
from routes.views_routes import views_bp

if 'users' not in app.blueprints:
    app.register_blueprint(users_bp)
    
if 'presentations' not in app.blueprints:
    app.register_blueprint(presentations_bp)
    
if 'queries' not in app.blueprints:
    app.register_blueprint(queries_bp)
    
if 'views' not in app.blueprints:
    app.register_blueprint(views_bp)
    
from controllers.auth_controller import login_manager

login_manager.init_app(app)
login_manager.login_view = 'login_get'   
    

if __name__ == "__main__":
    app.run(debug=True)
