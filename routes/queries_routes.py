from flask import Blueprint, render_template
from flask_login import login_required
from controllers.auth_controller import roles_required
from controllers.queries_controller import get_courses_with_available_spots

queries_bp = Blueprint('queries', __name__, url_prefix='/queries')

@queries_bp.route('/available-spots')
@login_required
@roles_required('admin', 'secretary')
def available_spots():
    courses = get_courses_with_available_spots()
    return render_template('queries/available_spots.html', courses=courses)
