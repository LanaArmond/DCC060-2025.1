from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from models import db


app = Flask(__name__)

# --- Config ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)



def show_tables():
    with db.engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
    print("Tables in the database:")
    for table in tables:
        print(f" - {table}")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        show_tables()  # <-- This will print your tables to the console
        # Optionally create tables if needed
        # db.create_all()
    app.run(debug=True)
