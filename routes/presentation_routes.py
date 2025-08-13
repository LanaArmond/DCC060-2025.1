from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from controllers.auth_controller import roles_required
from controllers.presentations_controller import (
    get_all_presentations,
    create_presentation,
    get_presentation,
    update_presentation,
    delete_presentation
)
from models import Amphitheater, Conductor, Student
from datetime import datetime

presentations_bp = Blueprint('presentations', __name__, url_prefix='/presentations')


@presentations_bp.route("/")
@login_required
# @roles_required("admin", "secretary")
def list_presentations():
    presentations = get_all_presentations()
    return render_template("presentations/list.html", presentations=presentations)


@presentations_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin", "secretary")
def create_presentation_route():
    amphitheaters = Amphitheater.query.all()
    conductors = Conductor.query.all()
    students = Student.query.all()

    if request.method == "POST":
        title = request.form.get("title")
        date_str = request.form.get("date")
        date = datetime.fromisoformat(date_str)
        level = int(request.form.get("level"))
        guest_number = int(request.form.get("guest_number"))
        amphitheater_id = int(request.form.get("amphitheater_id"))
        conductor_id = int(request.form.get("conductor_id"))
        student_ids = [int(sid) for sid in request.form.getlist("student_ids")]

        presentation, error = create_presentation(
            title, date, level, guest_number, amphitheater_id, conductor_id, student_ids
        )
        if error:
            flash(error, "danger")
            return redirect(url_for("presentations.create_presentation_route"))

        flash("Presentation created successfully", "success")
        return redirect(url_for("presentations.list_presentations"))

    return render_template("presentations/create.html", amphitheaters=amphitheaters, conductors=conductors, students=students)


@presentations_bp.route("/<int:presentation_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "secretary")
def edit_presentation_route(presentation_id):
    presentation = get_presentation(presentation_id)
    if not presentation:
        flash("Presentation not found", "danger")
        return redirect(url_for("presentations.list_presentations"))

    amphitheaters = Amphitheater.query.all()
    conductors = Conductor.query.all()
    students = Student.query.all()

    if request.method == "POST":
        title = request.form.get("title")
        date = datetime.fromisoformat(request.form.get("date"))
        level = int(request.form.get("level"))
        guest_number = int(request.form.get("guest_number"))
        amphitheater_id = int(request.form.get("amphitheater_id"))
        conductor_id = int(request.form.get("conductor_id"))
        student_ids = [int(sid) for sid in request.form.getlist("student_ids")]

        updated, error = update_presentation(
            presentation, title, date, level, guest_number, amphitheater_id, conductor_id, student_ids
        )
        if error:
            flash(error, "danger")
            return redirect(url_for("presentations.edit_presentation_route", presentation_id=presentation.id))

        flash("Presentation updated successfully", "success")
        return redirect(url_for("presentations.list_presentations"))

    return render_template("presentations/edit.html", presentation=presentation, amphitheaters=amphitheaters, conductors=conductors, students=students)


@presentations_bp.route("/<int:presentation_id>/delete", methods=["POST"])
@login_required
@roles_required("admin", "secretary")
def delete_presentation_route(presentation_id):
    presentation = get_presentation(presentation_id)
    if not presentation:
        flash("Presentation not found", "danger")
        return redirect(url_for("presentations.list_presentations"))

    delete_presentation(presentation)
    flash("Presentation deleted successfully", "success")
    return redirect(url_for("presentations.list_presentations"))
