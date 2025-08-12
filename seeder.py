# seeder.py
import random
from datetime import datetime, timedelta
from faker import Faker
from main import app, db 
from models import User, Admin, Worker, Student, Maintenancer, Professor, Secretary, Conductor, \
    Dependency, Amphitheater, Classroom, Course, Class, Enrollment, Attendance, Participation, \
    Instrument, Maintenance, Presentation, Rehearsal
from triggers import *
from sqlalchemy import text
from views import create_views

fake = Faker()

def seed_users(n=10):
    users = []
    for _ in range(n):
        user = User(
            name=fake.name(),
            email=fake.unique.email(),
            password=fake.password()
        )
        db.session.add(user)
        users.append(user)
    db.session.flush()
    return users

def seed_users(count=30):
    users = []
    for _ in range(count):
        user = User(
            name=fake.name(),
            email=fake.unique.email(),
            password=fake.password()
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
            student = Student(user_id=user.id, age=age, phone_number=phone)
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
    for _ in range(n):
        dep = Dependency(name=fake.unique.word())
        db.session.add(dep)
        deps.append(dep)
    db.session.flush()
    return deps

def seed_amphitheaters(deps):
    amphitheaters = []
    for dep in random.sample(deps, k=min(2, len(deps))):
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
    courses = []
    for prof in professors:
        course = Course(
            name=fake.word(),
            level=random.randint(0, 5),
            instrument_focus=fake.word(),
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

def seed_presentations(amphitheaters, conductors):
    presentations = []
    for _ in range(3):
        pres = Presentation(
            title=fake.sentence(),
            date=fake.date_time_between(start_date='-30d', end_date='+30d'),
            level=random.randint(0, 5),
            guest_number=random.randint(0, 200),
            amphitheater_id=random.choice(amphitheaters).id,
            conductor_id=random.choice(conductors).id
        )
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
        presentations = run_and_print(seed_presentations, amphitheaters, conductors)
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

