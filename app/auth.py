from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_jwt_extended import create_access_token

from . import db
from .models import User


auth_bp = Blueprint("auth", __name__)
api_auth_bp = Blueprint("api_auth", __name__, url_prefix="/api/auth")


def _current_user_is_admin() -> bool:
    return current_user.is_authenticated and (current_user.role or "").lower() == "admin"


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    total_users = User.query.count()
    is_initial_setup = total_users == 0

    if not current_user.is_authenticated and total_users > 0:
        flash("Please contact an administrator to create a new account.", "warning")
        return redirect(url_for("auth.login"))

    if current_user.is_authenticated and not _current_user_is_admin():
        flash("Only administrators can create new users.", "danger")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = (request.form.get("role") or "").strip()
        role = role or ("admin" if is_initial_setup else "user")

        if not username or not password:
            flash("Username and password are required.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
        else:
            user = User(username=username, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            if _current_user_is_admin():
                flash(f"User '{username}' added successfully.", "success")
                return redirect(url_for("main.manage"))
            flash("Registration successful. Please log in with your new credentials.", "success")
            return redirect(url_for("auth.login"))

    return render_template("register.html", is_initial_setup=is_initial_setup)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("main.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@api_auth_bp.post("/register")
def api_register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "user").strip() or "user"

    if not username or not password:
        return jsonify({"message": "Username and password are required."}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists."}), 400

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registration successful."}), 201


@api_auth_bp.post("/login")
def api_login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid credentials."}), 401

    token = create_access_token(identity=str(user.id), additional_claims={"username": user.username, "role": user.role})
    return jsonify({"access_token": token, "user": {"username": user.username, "role": user.role}})
