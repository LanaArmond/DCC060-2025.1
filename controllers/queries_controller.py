from main import db
from models import Course
from sqlalchemy import func
from sqlalchemy.sql import text

def get_courses_with_available_spots():
    query = text("""
        SELECT 
            c.name,
            c.level,
            COUNT(e.student_id) AS current_enrollments,
            (c.student_limit - COUNT(e.student_id)) AS available_spots
        FROM course c
        LEFT JOIN enrollment e ON c.id = e.course_id
        GROUP BY c.id, c.name, c.level, c.instrument_focus, c.student_limit
        HAVING COUNT(e.student_id) < c.student_limit
        ORDER BY available_spots DESC;
    """)
    result = db.session.execute(query)
    courses = [dict(row) for row in result.mappings()]
    return courses

