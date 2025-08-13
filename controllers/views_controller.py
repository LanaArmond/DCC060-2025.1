from main import db
from sqlalchemy import text

def get_all_classes_schedule():
    result = db.session.execute(text("SELECT * FROM vw_agenda_aulas"))
    return [dict(row._mapping) for row in result]