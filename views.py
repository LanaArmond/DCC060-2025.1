from main import db
from sqlalchemy import text

def create_views():
    with db.engine.connect() as conn:
        conn.execute(text("DROP VIEW IF EXISTS vw_agenda_aulas"))
        conn.execute(text("""
            CREATE VIEW vw_agenda_aulas AS
            SELECT 
                cl.date AS data_hora,
                c.name AS curso,
                d.name AS sala,
                u.name AS professor
            FROM class cl
            JOIN course c ON cl.course_id = c.id
            JOIN classroom cr ON cl.classroom_id = cr.id
            JOIN dependency d ON cr.dependency_id = d.id
            JOIN professor p ON c.professor_id = p.id
            JOIN worker w ON p.worker_id = w.id
            JOIN user u ON w.user_id = u.id
        """))

        conn.execute(text("DROP VIEW IF EXISTS vw_participacao_apresentacoes"))
        conn.execute(text("""
            CREATE VIEW vw_participacao_apresentacoes AS
            SELECT 
                s.id AS student_id,
                u.name AS aluno,
                COUNT(p.id) AS total_apresentacoes
            FROM user u
            JOIN student s ON u.id = s.user_id
            LEFT JOIN participation part ON s.id = part.student_id
            LEFT JOIN presentation p ON part.presentation_id = p.id
            GROUP BY s.id, u.name
        """))

        conn.execute(text("DROP VIEW IF EXISTS vw_cursos_com_vagas"))
        conn.execute(text("""
            CREATE VIEW vw_cursos_com_vagas AS
            SELECT 
                c.name,
                c.student_limit - COUNT(e.student_id) AS vagas
            FROM course c
            LEFT JOIN enrollment e ON c.id = e.course_id
            GROUP BY c.student_limit, c.name
            HAVING vagas > 0
        """))

def drop_views():
    with db.engine.connect() as conn:
        conn.execute(text("DROP VIEW IF EXISTS vw_agenda_aulas"))
        conn.execute(text("DROP VIEW IF EXISTS vw_participacao_apresentacoes"))
        conn.execute(text("DROP VIEW IF EXISTS vw_cursos_com_vagas"))

if __name__ == "__main__":
    with db.engine.begin() as conn:
        create_views()
    print("Views created successfully.")
