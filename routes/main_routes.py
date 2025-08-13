from flask import render_template, request, redirect, url_for
from main import app
from controllers.auth_controller import authenticate, login, logout, is_logged_in
from flask_login import login_required, current_user

@app.route("/")
def home():
    if is_logged_in():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login_get"))

@app.route("/login", methods=["GET"])
def login_get():
    if is_logged_in():
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("email")
    password = request.form.get("password")
    user = authenticate(username, password)
    if user:
        login(user)
        return redirect(url_for("dashboard"))
    else:
        return render_template("login.html", error="Invalid credentials.")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

@app.route("/logout")
@login_required
def logout_route():
    logout()
    return redirect(url_for("login_get"))
