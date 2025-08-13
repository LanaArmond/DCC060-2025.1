from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    _password = db.Column("password", db.String(255), nullable=False)

    admin = db.relationship("Admin", back_populates="user", uselist=False)
    worker = db.relationship("Worker", back_populates="user", uselist=False)
    student = db.relationship("Student", back_populates="user", uselist=False)

    @property
    def password(self):
        return self.__dict__['password']

    @password.setter
    def password(self, raw_password):
        self._password = generate_password_hash(raw_password)

    def check_password(self, password):
        print(self._password, password)
        return check_password_hash(self._password, password)


class Admin(db.Model):
    __tablename__ = 'admin'
    user_id = db.Column(db.Integer, ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, unique=True)
    user = db.relationship("User", back_populates="admin")


class Worker(db.Model):
    __tablename__ = 'worker'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), unique=True, nullable=False)
    salary = db.Column(db.Float, nullable=False)
    __table_args__ = (CheckConstraint('salary >= 0'),)
    user = db.relationship("User", back_populates="worker")
    maintenancer = db.relationship("Maintenancer", back_populates="worker", uselist=False)
    professor = db.relationship("Professor", back_populates="worker", uselist=False)
    secretary = db.relationship("Secretary", back_populates="worker", uselist=False)


class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), unique=True, nullable=False)
    age = db.Column(db.Integer)
    phone_number = db.Column(db.String(20))
    level = db.Column(db.SmallInteger, nullable=False)
    
    __table_args__ = (CheckConstraint('level BETWEEN 0 AND 5'),)
    __table_args__ = (CheckConstraint('age BETWEEN 10 AND 85'),)
    
    user = db.relationship("User", back_populates="student")
    
    presentations = db.relationship(
        'Presentation',
        secondary='participation',
        back_populates='students'
    )

class Maintenancer(db.Model):
    __tablename__ = 'maintenancer'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    worker_id = db.Column(db.Integer, ForeignKey('worker.id', ondelete='CASCADE', onupdate='CASCADE'), unique=True, nullable=False)
    outsourced_worker = db.Column(db.Boolean, nullable=False)
    worker = db.relationship("Worker", back_populates="maintenancer")


class Professor(db.Model):
    __tablename__ = 'professor'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    worker_id = db.Column(db.Integer, ForeignKey('worker.id', ondelete='CASCADE', onupdate='CASCADE'), unique=True, nullable=False)
    academic_bg = db.Column(db.Text, nullable=False)
    worker = db.relationship("Worker", back_populates="professor")
    conductor = db.relationship("Conductor", uselist=False, back_populates="professor")


class Secretary(db.Model):
    __tablename__ = 'secretary'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    worker_id = db.Column(db.Integer, ForeignKey('worker.id', ondelete='CASCADE', onupdate='CASCADE'), unique=True, nullable=False)
    sector = db.Column(db.String(50))
    worker = db.relationship("Worker", back_populates="secretary")


class Conductor(db.Model):
    __tablename__ = 'conductor'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    professor_id = db.Column(db.Integer, ForeignKey('professor.id', ondelete='CASCADE', onupdate='CASCADE'), unique=True, nullable=False)
    level = db.Column(db.SmallInteger, nullable=False)
    __table_args__ = (CheckConstraint('level BETWEEN 0 AND 5'),)
    
    professor = db.relationship("Professor", back_populates="conductor")


class Dependency(db.Model):
    __tablename__ = 'dependency'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    
    amphitheater = db.relationship("Amphitheater", back_populates="dependency", uselist=False)
    classrooms = db.relationship("Classroom", back_populates="dependency", uselist=False)


class Amphitheater(db.Model):
    __tablename__ = 'amphitheater'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    dependency_id = db.Column(db.Integer, ForeignKey('dependency.id', ondelete='CASCADE', onupdate='CASCADE'), unique=True, nullable=False)
    guest_capacity = db.Column(db.Integer, nullable=False)
    __table_args__ = (CheckConstraint('guest_capacity > 0'),)

    dependency = db.relationship("Dependency", back_populates="amphitheater")


class Classroom(db.Model):
    __tablename__ = 'classroom'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    dependency_id = db.Column(db.Integer, ForeignKey('dependency.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    ac_insulation = db.Column(db.Boolean, nullable=False)

    dependency = db.relationship("Dependency", back_populates="classrooms")

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    level = db.Column(db.SmallInteger, nullable=False, index=True)
    instrument_focus = db.Column(db.String(100), nullable=False)
    student_limit = db.Column(db.Integer, nullable=False)
    professor_id = db.Column(db.Integer, ForeignKey('professor.id', ondelete='SET NULL', onupdate='CASCADE'), unique=False, nullable=True)
    __table_args__ = (
        CheckConstraint('level BETWEEN 0 AND 5'),
        CheckConstraint('student_limit > 0'),
    )
    

class Class(db.Model):
    __tablename__ = 'class'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime, nullable=False)
    classroom_id = db.Column(db.Integer, ForeignKey('classroom.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, ForeignKey('course.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)


class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    student_id = db.Column(db.Integer, ForeignKey('student.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    course_id = db.Column(db.Integer, ForeignKey('course.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)


class Attendance(db.Model):
    __tablename__ = 'attendance'
    student_id = db.Column(db.Integer, ForeignKey('student.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    class_id = db.Column(db.Integer, ForeignKey('class.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)


class Participation(db.Model):
    __tablename__ = 'participation'
    student_id = db.Column(db.Integer, ForeignKey('student.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    presentation_id = db.Column(db.Integer, ForeignKey('presentation.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)


class Instrument(db.Model):
    __tablename__ = 'instrument'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status = db.Column(db.String(20), nullable=False)
    dependency_id = db.Column(db.Integer, ForeignKey('dependency.id', ondelete='SET NULL', onupdate='CASCADE'))


class Maintenance(db.Model):
    __tablename__ = 'maintenance'
    instrument_id = db.Column(db.Integer, ForeignKey('instrument.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    maintenancer_id = db.Column(db.Integer, ForeignKey('maintenancer.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)


class Presentation(db.Model):
    __tablename__ = 'presentation'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    level = db.Column(db.SmallInteger, nullable=False)
    guest_number = db.Column(db.Integer, nullable=False)
    amphitheater_id = db.Column(db.Integer, db.ForeignKey('amphitheater.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductor.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    
    __table_args__ = (
        CheckConstraint('level BETWEEN 0 AND 5'),
        CheckConstraint('guest_number >= 0'),
    )
    
    # Relationship to students via association table
    students = db.relationship(
        'Student',
        secondary='participation',
        back_populates='presentations'
    )
    
    conductor = db.relationship("Conductor", backref="presentations")
    amphitheater = db.relationship("Amphitheater", backref="presentations")


class Rehearsal(db.Model):
    __tablename__ = 'rehearsal'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime, nullable=False)
    amphitheater_id = db.Column(db.Integer, ForeignKey('amphitheater.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    presentation_id = db.Column(db.Integer, ForeignKey('presentation.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
