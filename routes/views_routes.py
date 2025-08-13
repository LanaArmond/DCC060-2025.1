from flask import Blueprint, render_template
from flask_login import login_required
from controllers.auth_controller import roles_required
from controllers.views_controller import get_all_classes_schedule

views_bp = Blueprint('views', __name__, url_prefix='/views')

@views_bp.route('/agenda-aulas')
@login_required
def classes_schedule():
    agenda = get_all_classes_schedule()
    return render_template('views/classes_schedule.html', agenda=agenda)
