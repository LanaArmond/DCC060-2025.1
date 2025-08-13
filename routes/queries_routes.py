from flask import Blueprint, render_template, request, flash
from flask_login import login_required
from controllers.auth_controller import roles_required
from controllers.queries_controller import get_courses_with_available_spots, get_students_never_participated, execute_query, get_predefined_queries

queries_bp = Blueprint('queries', __name__, url_prefix='/queries')

@queries_bp.route('/available-spots')
@login_required
def available_spots():
    courses = get_courses_with_available_spots()
    return render_template('queries/available_spots.html', courses=courses)

@queries_bp.route("/students/no_participation")
@login_required
@roles_required("admin", "secretary")
def students_never_participated():
    students = get_students_never_participated()
    return render_template("queries/students_no_participation.html", students=students)


@queries_bp.route('/querymaker', methods=['GET', 'POST'])
@login_required
def querymaker():
    queries = get_predefined_queries()
    results = None
    error = None
    explain_plan = None
    query = ''

    if request.method == 'POST':
        query = request.form.get('sql_query', '')
        results, error, explain_plan = execute_query(query)
        if error:
            flash(f"Error executing query: {error}", 'danger')

    return render_template(
        'queries/querymaker.html',
        queries=queries,
        results=results,
        error=error,
        explain_plan=explain_plan,
        query=query
    )
