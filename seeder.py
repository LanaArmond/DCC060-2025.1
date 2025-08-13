# seeder.py
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

fake = Faker()

def seed_users(count=30):
    users = []
    for _ in range(count):
        user = User(
            name=fake.name(),
            email=fake.unique.email(),
            password="123456"
        )
        users.append(user)
        db.session.add(user)
    db.session.commit()
    return users

def seed_user_specializations(users):
    admins = []
    workers = []
    students = []

    if not users:
        raise ValueError("No users available to assign specializations")

    # Calculate the split points
    total_users = len(users)
    split1 = total_users // 3
    split2 = 2 * total_users // 3

    for i, user in enumerate(users):
        if i < split1:
            # First third become admins
            admin = Admin(user_id=user.id)
            db.session.add(admin)
            admins.append(admin)
        elif i < split2:
            # Second third become workers
            salary = round(random.uniform(1000, 5000), 2)
            worker = Worker(user_id=user.id, salary=salary)
            db.session.add(worker)
            workers.append(worker)
        else:
            # Last third become students
            age = random.randint(10, 85)
            phone = fake.phone_number()
            student = Student(user_id=user.id, age=age, phone_number=phone, level=random.randint(0, 5))
            db.session.add(student)
            students.append(student)

    db.session.commit()
    return admins, workers, students


def seed_worker_specializations():
    professors = []
    secretaries = []
    maintenancers = []

    workers = Worker.query.all()
    if not workers:
        raise ValueError("No workers available to assign specializations")

    # Calculate the split points
    total_workers = len(workers)
    split1 = total_workers // 3
    split2 = 2 * total_workers // 3

    for i, worker in enumerate(workers):
        if i < split1:
            # First third become professors
            prof = Professor(
                worker_id=worker.id,
                academic_bg=fake.text(max_nb_chars=100)
            )
            db.session.add(prof)
            professors.append(prof)
        elif i < split2:
            # Second third become secretaries
            secretary = Secretary(
                worker_id=worker.id,
                sector=fake.job()
            )
            db.session.add(secretary)
            secretaries.append(secretary)
        else:
            # Last third become maintenancers
            maint = Maintenancer(
                worker_id=worker.id,
                outsourced_worker=random.choice([True, False])
            )
            db.session.add(maint)
            maintenancers.append(maint)

    db.session.commit()
    return professors, secretaries, maintenancers

def seed_conductors(professors):
    conductors = []
    for prof in professors:
        conductor = Conductor(professor_id=prof.id, level=random.randint(0, 5))
        db.session.add(conductor)
        conductors.append(conductor)
    db.session.flush()
    return conductors

def seed_dependencies(n=5):
    deps = []
    suffixes = ['Hall', 'Center', 'Theater', 'Auditorium', 'Stage', 'Venue']
    for _ in range(n):
        # Generate a location or building-related word from faker
        place = fake.city()  # or fake.street_name(), fake.word(), fake.last_name() etc.
        suffix = random.choice(suffixes)
        # Combine for a coherent amphitheater dependency name
        name = f"{place} {suffix}"
        dep = Dependency(name=name)
        db.session.add(dep)
        deps.append(dep)
    db.session.flush()
    return deps

def seed_amphitheaters(deps):
    amphitheaters = []
    for dep in random.sample(deps, k=min(4, len(deps))):
        amph = Amphitheater(
            dependency_id=dep.id, 
            guest_capacity=random.randint(50, 300)
        )
        db.session.add(amph)
        amphitheaters.append(amph)
    db.session.flush()
    return amphitheaters

def seed_classrooms(deps):
    classrooms = []
    for dep in random.sample(deps, k=min(2, len(deps))):
        classroom = Classroom(
            dependency_id=dep.id, 
            ac_insulation=random.choice([True, False])
        )
        db.session.add(classroom)
        classrooms.append(classroom)
    db.session.flush()
    return classrooms

def seed_courses(professors):
    instrument_options = ["Violin", "Piano", "Flute", "Cello", "Harp", "Clarinet"]

    # Level-specific course name templates
    level_course_names = {
        0: [  # Básico
            "{} Fundamentals",
            "Basics of {}",
            "Intro to {}"
        ],
        1: [  # Iniciante
            "Beginner's Guide to {}",
            "{} for Starters",
            "Getting Started with {}"
        ],
        2: [  # Aprendiz
            "{} Apprenticeship",
            "Apprentice {} Techniques",
            "Developing {} Skills"
        ],
        3: [  # Intermediário
            "Intermediate {} Studies",
            "Building {} Techniques",
            "{} Ensemble Playing"
        ],
        4: [  # Avançado
            "Advanced {} Techniques",
            "Mastering {}",
            "Advanced {} Workshop"
        ],
        5: [  # Virtuoso
            "Virtuoso {} Masterclass",
            "Concert-Level {} Performance",
            "Virtuoso {} Techniques"
        ]
    }

    courses = []
    for prof in professors:
        level = random.randint(0, 5)
        instrument = random.choice(instrument_options)
        name_template = random.choice(level_course_names[level])
        name = name_template.format(instrument)

        course = Course(
            name=name,
            level=level,
            instrument_focus=instrument,
            student_limit=random.randint(5, 30),
            professor_id=prof.id
        )
        db.session.add(course)
        courses.append(course)

    db.session.flush()
    return courses


def seed_classes(classrooms, courses):
    classes = []
    for _ in range(5):
        cls = Class(
            date=fake.date_time_between(start_date='-30d', end_date='+30d'),
            classroom_id=random.choice(classrooms).id,
            course_id=random.choice(courses).id
        )
        db.session.add(cls)
        classes.append(cls)
    db.session.flush()
    return classes

def seed_enrollments(students, courses):
    for student in students:
        for course in random.sample(courses, k=1):
            db.session.add(Enrollment(student_id=student.id, course_id=course.id))

def seed_attendance(students, classes):
    for cls in classes:
        for student in random.sample(students, k=min(2, len(students))):
            db.session.add(Attendance(student_id=student.id, class_id=cls.id))

def seed_instruments(deps):
    instruments = []
    
    for _ in range(3):
        instr = Instrument(
            status='APTO',
            dependency_id=random.choice(deps).id
        )
        db.session.add(instr)
        instruments.append(instr)
    
    for _ in range(1):
        instr = Instrument(
            status='EM_MANUTENCAO',
            dependency_id=None
        )
        db.session.add(instr)
        instruments.append(instr)
    
    for _ in range(1):
        instr = Instrument(
            status='DESATIVADO',
            dependency_id=None
        )
        db.session.add(instr)
        instruments.append(instr)
    
    db.session.flush()
    return instruments

def seed_maintenance(instruments, maintenancers):
    for instr in instruments:
        if instr.status == 'EM_MANUTENCAO':
            maint = random.choice(maintenancers)
            db.session.add(Maintenance(
                instrument_id=instr.id,
                maintenancer_id=maint.id,
            ))
    
    db.session.flush()

def seed_presentations(amphitheaters):
    presentations = []

    for _ in range(3):
        amphitheater = random.choice(amphitheaters)

        guest_number = random.randint(0, amphitheater.guest_capacity)

        level = random.randint(0, 5)

        days_ahead = random.randint(-30, 30)
        base_date = datetime.now() + timedelta(days=days_ahead)
        base_date += timedelta(days=(5 - base_date.weekday()) % 7)
        hour = random.randint(14, 22)
        date = datetime.combine(base_date.date(), time(hour=hour, minute=0))

        conductor_user = User(
            name=fake.name(),
            email=fake.unique.email(),
            password="123456"
        )
        db.session.add(conductor_user)
        db.session.flush()
        
        salary = round(random.uniform(1000, 5000), 2)
        worker = Worker(user_id=conductor_user.id, salary=salary)
        db.session.add(worker)
        db.session.flush()
    
        professor = Professor(
            worker_id=worker.id,
            academic_bg=fake.text(max_nb_chars=100)
        )
        db.session.add(professor)
        db.session.flush()

        conductor = Conductor(
            professor_id=professor.id,
            level=random.randint(level, 5)
        )
        db.session.add(conductor)
        db.session.flush()

        students = []
        for _ in range(random.randint(5, 15)):
            student_user = User(
                name=fake.name(),
                email=fake.unique.email(),
                password="123456"
            )
            db.session.add(student_user)
            db.session.flush()

            student = Student(
                user_id=student_user.id,
                age=random.randint(10, 85),
                phone_number=fake.phone_number(),
                level=random.randint(level, 5)
            )
            db.session.add(student)
            students.append(student)

        music_titles = [
            "Symphony Under the Stars",
            "Jazz & Moonlight",
            "Echoes of the Violin",
            "Harmony of the Winds",
            "Piano Nights",
            "The Choral Journey",
            "Strings & Serenades",
            "Rhythms of the World",
            "Opera in the Park",
            "Ballads and Beyond"
        ]
        title = random.choice(music_titles)

        pres = Presentation(
            title=title,
            date=date,
            level=level,
            guest_number=guest_number,
            amphitheater_id=amphitheater.id,
            conductor_id=conductor.id
        )
        pres.students = students

        db.session.add(pres)
        presentations.append(pres)

    db.session.flush()
    return presentations


def seed_participations(students, presentations):
    for pres in presentations:
        for student in random.sample(students, k=min(2, len(students))):
            db.session.add(Participation(student_id=student.id, presentation_id=pres.id))

def seed_rehearsals(amphitheaters, presentations):
    for pres in presentations:
        db.session.add(Rehearsal(
            date=fake.date_time_between(start_date='-10d', end_date='+10d'),
            amphitheater_id=random.choice(amphitheaters).id,
            presentation_id=pres.id
        ))

def run_and_print(func, *args):
    print(f"📌 Running {func.__name__}...")
    return func(*args)

def seed_all():
    with app.app_context():
        db.drop_all()
        db.create_all()

        users = run_and_print(seed_users)
        admins, workers, students = run_and_print(seed_user_specializations, users)
        professors, secretaries, maintenancers = run_and_print(seed_worker_specializations)             
        conductors = run_and_print(seed_conductors, professors)
        deps = run_and_print(seed_dependencies)
        amphitheaters = run_and_print(seed_amphitheaters, deps)
        classrooms = run_and_print(seed_classrooms, deps)
        instruments = run_and_print(seed_instruments, deps)
        courses = run_and_print(seed_courses, professors)
        classes = run_and_print(seed_classes, classrooms, courses)
        run_and_print(seed_enrollments, students, courses)
        run_and_print(seed_attendance, students, classes)
        run_and_print(seed_maintenance, instruments, maintenancers)
        presentations = run_and_print(seed_presentations, amphitheaters)
        run_and_print(seed_participations, students, presentations)
        run_and_print(seed_rehearsals, amphitheaters, presentations)

        db.session.commit()
        

def reset_and_seed():
    """Empties the database and calls seed_all()."""
    print("Dropping all tables...")
    db.drop_all()

    print("Creating all tables (triggers will be created automatically)...")
    db.create_all()  # triggers created here due to event.listen
    
    
    print("Creating views")
    create_views()

    print("Seeding database...")
    seed_all()
    
    

    print("Database reset and seeded successfully.")


if __name__ == "__main__":
    with app.app_context():
        reset_and_seed()

