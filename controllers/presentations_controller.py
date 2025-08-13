from datetime import time
from main import db
from models import Presentation, Amphitheater, Conductor, Student
from sqlalchemy.orm import joinedload


def validate_presentation_data(title, date, level, guest_number, amphitheater_id, conductor_id, student_ids):
    # 1. Check time constraints (only weekends between 14h and 22h)
    if date.weekday() not in (5, 6):  # 5 = Saturday, 6 = Sunday
        return None, "Presentations can only be scheduled on weekends."
    if not (time(14, 0) <= date.time() <= time(22, 0)):
        return None, "Presentation time must be between 14:00 and 22:00."

    # 2. Amphitheater guest capacity
    amphitheater = Amphitheater.query.get(amphitheater_id)
    if not amphitheater:
        return None, "Amphitheater not found."
    if amphitheater.guest_capacity < guest_number:
        return None, "Amphitheater cannot hold the specified guest number."

    # 3. Conductor level requirement
    conductor = Conductor.query.get(conductor_id)
    if not conductor:
        return None, "Conductor not found."
    if conductor.level < level:
        return None, "Conductor level is too low for this presentation."

    # 4. Student level requirement
    students = Student.query.filter(Student.id.in_(student_ids)).all()
    if len(students) != len(student_ids):
        return None, "Some students not found."
    for student in students:
        if student.level < level:
            return None, f"Student {student.id} level is too low for this presentation."

    return (amphitheater, conductor, students), None


def get_all_presentations():
    return Presentation.query.options(
        joinedload(Presentation.students),
        joinedload(Presentation.conductor),
        joinedload(Presentation.amphitheater)
    ).all()


def create_presentation(title, date, level, guest_number, amphitheater_id, conductor_id, student_ids):
    validated, error = validate_presentation_data(
        title, date, level, guest_number, amphitheater_id, conductor_id, student_ids
    )
    if error:
        return None, error

    amphitheater, conductor, students = validated

    presentation = Presentation(
        title=title,
        date=date,
        level=level,
        guest_number=guest_number,
        amphitheater_id=amphitheater.id,
        conductor_id=conductor.id
    )
    presentation.students.extend(students)
    db.session.add(presentation)
    db.session.commit()
    return presentation, None


def get_presentation(presentation_id):
    return Presentation.query.get(presentation_id)


def update_presentation(presentation, title, date, level, guest_number, amphitheater_id, conductor_id, student_ids):
    validated, error = validate_presentation_data(
        title, date, level, guest_number, amphitheater_id, conductor_id, student_ids
    )
    if error:
        return None, error

    amphitheater, conductor, students = validated

    presentation.title = title
    presentation.date = date
    presentation.level = level
    presentation.guest_number = guest_number
    presentation.amphitheater_id = amphitheater.id
    presentation.conductor_id = conductor.id
    presentation.students = students  # overwrite relationship
    db.session.commit()
    return presentation, None


def delete_presentation(presentation):
    db.session.delete(presentation)
    db.session.commit()
