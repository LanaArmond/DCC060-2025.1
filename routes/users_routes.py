from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from controllers.auth_controller import roles_required, current_user
from controllers.users_controller import get_all_users, create_user, get_user, update_user, delete_user

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route("/")
@login_required
@roles_required("admin", "secretary")
def list_users():
    users = get_all_users()
    return render_template("users/list.html", users=users)

@users_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin", "secretary")
def create_user_route():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        user, error = create_user(name, email, password)
        if error:
            flash(error, "danger")
            return redirect(url_for("users.create_user_route"))
        flash("User created successfully", "success")
        return redirect(url_for("users.list_users"))
    return render_template("users/create.html")

@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "secretary")
def edit_user_route(user_id):
    user = get_user(user_id)
    if not user:
        flash("User not found", "danger")
        return redirect(url_for("users.list_users"))
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        update_user(user, name, email, password)
        flash("User updated successfully", "success")
        return redirect(url_for("users.list_users"))
    return render_template("users/edit.html", user=user)

@users_bp.route("/<int:user_id>/delete", methods=["POST"])
@login_required
@roles_required("admin", "secretary")
def delete_user_route(user_id):
    user = get_user(user_id)
    if not user:
        flash("User not found", "danger")
        return redirect(url_for("users.list_users"))
    delete_user(user)
    flash("User deleted successfully", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/me", methods=["GET", "POST"])
@login_required
def profile():
    user = get_user(current_user.id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")  # Optional: allow empty to keep current password

        update_user(user, name, email, password)
        flash("Profile updated successfully.", "success")
        return redirect(url_for("users.profile"))

    return render_template("users/profile.html", user=user)