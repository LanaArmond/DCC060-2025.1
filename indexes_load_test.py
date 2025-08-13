import random
from datetime import datetime, timedelta, time
from faker import Faker
from main import app, db 
from models import User, Admin, Worker, Student, Maintenancer, Professor, Secretary, Conductor, \
    Dependency, Amphitheater, Classroom, Course, Class, Enrollment, Attendance, Participation, \
    Instrument, Maintenance, Presentation, Rehearsal
from triggers import *
from sqlalchemy import text
from views import create_views
from seeder import *
from tqdm import tqdm


def seed_courses_simple(quantity):
    instrument_options = ["Violin", "Piano", "Flute", "Cello", "Harp", "Clarinet"]

    for i in tqdm(range(quantity), desc="Seeding Courses"):
        level = random.randint(0, 5)
        instrument = random.choice(instrument_options)
        name = f"{instrument} Course {i+1}"

        course = Course(
            name=name,
            level=level,
            instrument_focus=instrument,
            student_limit=random.randint(5, 30),
            professor_id=None  # assign professor_id if needed
        )
        db.session.add(course)
    
    db.session.commit()


def seed_users_simple(quantity):
    for i in tqdm(range(quantity), desc="Seeding Users"):
        user = User(
            name=f"Test User {i+1}",
            email=f"testuser{i+1}@example.com",
            password="123456"
        )
        db.session.add(user)
    
    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        reset_and_seed()
        print("Starting user overload...")
        seed_users_simple(10_000)
        print("starting course overload...")
        seed_courses_simple(10_000)

        db.session.commit()
    print("Database overloaded with users and courses!")