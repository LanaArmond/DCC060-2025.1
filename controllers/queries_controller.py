from main import db
from models import Course
from sqlalchemy import func
from sqlalchemy.sql import text
import re

def get_courses_with_available_spots():
    query = text(PREDEFINED_QUERIES["CONSULTA 01: Cursos com vagas disponíveis"])
    result = db.session.execute(query)
    courses = [dict(row) for row in result.mappings()]
    return courses



def get_students_never_participated():
    sql = text(PREDEFINED_QUERIES["CONSULTA 03: Alunos que nunca participaram de apresentações"])
    result = db.session.execute(sql)
    return [dict(row) for row in result.mappings()]


def execute_query(sql_query):
    if not sql_query.strip().lower().startswith('select'):
        return None, "Only SELECT queries are allowed", None

    try:
        # Get query plan (no timing info)
        explain_result = db.session.execute(text(f"EXPLAIN {sql_query}"))
        explain_plan = [dict(row._mapping) for row in explain_result]

        # Execute the actual query
        result = db.session.execute(text(sql_query))
        rows = result.fetchall()
        keys = result.keys()
        data = [dict(zip(keys, row)) for row in rows]

        return data, None, explain_plan
    except Exception as e:
        return None, str(e), None

def get_predefined_queries():
    """Retorna uma lista de tuplas (título, sql) das consultas pré-definidas."""
    return list(PREDEFINED_QUERIES.items())


PREDEFINED_QUERIES = {
    "CONSULTA 01: Cursos com vagas disponíveis": """
SELECT 
    c.name,
    c.level,
    COUNT(e.student_id) AS Current_Enrollments,
    (c.student_limit - COUNT(e.student_id)) AS Available_Spots
FROM course c
LEFT JOIN enrollment e 
    ON c.id = e.course_id
GROUP BY 
    c.id, c.name, c.level, c.instrument_focus, c.student_limit
HAVING 
    COUNT(e.student_id) < c.student_limit
ORDER BY Available_Spots DESC;
""",

    "CONSULTA 02: Cursos de nível intermediário (3) ou avançado (4)": """
SELECT c.name as curso, c.level
FROM course c
WHERE c.level BETWEEN 3 AND 4
ORDER BY c.level DESC;
""",

    "CONSULTA 03: Alunos que nunca participaram de apresentações": """
SELECT u.name AS aluno
FROM user u
INNER JOIN student s ON u.id = s.user_id
WHERE s.id NOT IN (
    SELECT student_id FROM participation
);
""",

    "CONSULTA 04: Número médio de alunos por curso": """
SELECT AVG(student_count) AS avg_students_per_course
FROM (
    SELECT e.course_id, COUNT(e.student_id) AS student_count
    FROM enrollment e
    GROUP BY e.course_id
) AS counts;
""",

    "CONSULTA 05: Apresentações com mais de 50 convidados": """
SELECT p.title, p.guest_number, a.guest_capacity
FROM presentation p
INNER JOIN amphitheater a ON p.amphitheater_id = a.id
WHERE p.guest_number > 50
AND p.guest_number <= a.guest_capacity;
""",

    "CONSULTA 06: Total de salas com isolamento acústico": """
SELECT COUNT(*) AS salas_isoladas
FROM classroom
WHERE ac_insulation = true;
""",

    "CONSULTA 07: Alunos matriculados em Cursos com foco em violino ou piano": """
SELECT DISTINCT u.name AS aluno
FROM user u
INNER JOIN student s ON u.id = s.user_id
INNER JOIN enrollment e ON s.id = e.student_id
INNER JOIN course c ON e.course_id = c.id
WHERE c.instrument_focus IN ('Violin', 'Piano');
""",

    "CONSULTA 08: Maestros e seus níveis de especialização": """
SELECT u.name AS maestro, c.level,
       CASE 
           WHEN c.level >= 4 THEN 'Avançado'
           ELSE 'Intermediário'
       END AS categoria
FROM user u
INNER JOIN worker w ON u.id = w.user_id
INNER JOIN professor p ON w.id = p.worker_id
INNER JOIN conductor c ON p.id = c.professor_id
ORDER BY c.level ASC;
""",

    "CONSULTA 09: Dependências não utilizadas": """
SELECT d.name AS dependencia_nao_utilizada
FROM dependency d
LEFT JOIN classroom cl ON d.id = cl.dependency_id
LEFT JOIN amphitheater a ON d.id = a.dependency_id
WHERE cl.dependency_id IS NULL 
AND a.dependency_id IS NULL;
""",

    "CONSULTA 10: Relatório completo de apresentações": """
SELECT p.title AS apresentacao,
       p.date AS data,
       d.name AS local,
       u_prof.name AS maestro,
       COUNT(part.student_id) AS participantes,
       p.guest_number AS convidados
FROM presentation p
INNER JOIN amphitheater a ON p.amphitheater_id = a.id
INNER JOIN dependency d ON a.dependency_id = d.id
INNER JOIN conductor c ON p.conductor_id = c.id
INNER JOIN professor prof ON c.professor_id = prof.id
INNER JOIN worker w ON prof.worker_id = w.id
INNER JOIN user u_prof ON w.user_id = u_prof.id
LEFT JOIN participation part ON p.id = part.presentation_id
GROUP BY p.id, d.name, u_prof.name
ORDER BY p.date ASC;
""",

    "CONSULTA 11: Alunos em Apresentações de Nível 5": """
SELECT u.name
FROM user u
JOIN student s ON u.id = s.user_id
WHERE EXISTS (
    SELECT 1
    FROM participation p
    JOIN presentation pr ON p.presentation_id = pr.id
    WHERE p.student_id = s.id AND pr.level = 5
);
""",

    "CONSULTA 12: Resumo de Matrículas por Nível": """
SELECT CONCAT('Nível ', c.level) AS categoria,
       COUNT(e.student_id) AS matriculas
FROM course c
LEFT JOIN enrollment e ON c.id = e.course_id
GROUP BY c.level

UNION ALL

SELECT 'Total Geral' AS categoria,
       COUNT(e.student_id) AS matriculas
FROM course c
LEFT JOIN enrollment e ON c.id = e.course_id;
""",

    "CONSULTA 13: Instrumentos em manutenção": """
SELECT i.id, i.status
FROM instrument i
WHERE i.status <> 'APTO';
""",

    "CONSULTA 14: Dependências sem instrumentos alocados": """
SELECT d.name
FROM dependency d
LEFT JOIN instrument i ON d.id = i.dependency_id
WHERE i.id IS NULL;
""",

    "CONSULTA 15: Histórico de manutenções por instrumento": """
SELECT 
    i.id AS instrumento, 
    COUNT(m.instrument_id) AS total_manutencoes
FROM instrument i
LEFT JOIN maintenance m ON i.id = m.instrument_id
GROUP BY i.id
ORDER BY total_manutencoes DESC;
""",

    "Agenda de Aulas (View)": """
    SELECT *, 'vw_agenda_aulas' AS source_view FROM vw_agenda_aulas;
""",

    "Participação em Apresentações (View)": """
    SELECT *, 'vw_participacao_apresentacoes' AS source_view FROM vw_participacao_apresentacoes;
""",

    "Cursos com Vagas (View)": """
    SELECT *, 'vw_cursos_com_vagas' AS source_view FROM vw_cursos_com_vagas;
"""
}
