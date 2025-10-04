from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .models import Employee, LeaveRequest, User


main_bp = Blueprint("main", __name__)


def _current_user_is_admin() -> bool:
    return (current_user.role or "").lower() == "admin"


@main_bp.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    if _current_user_is_admin():
        employees = Employee.query.order_by(Employee.id.asc()).all()
        leave_requests = (
            LeaveRequest.query.order_by(LeaveRequest.status.asc(), LeaveRequest.requested_at.desc()).all()
        )
        pending_count = sum(1 for req in leave_requests if req.status == "pending")
        admin_count = User.query.filter(User.role.ilike("admin")).count()
        return render_template(
            "index.html",
            employees=employees,
            admin_count=admin_count,
            leave_requests=leave_requests,
            pending_count=pending_count,
        )

    employee = current_user.employee_profile

    if request.method == "POST":
        if not employee:
            flash("Your employee profile is not set up yet. Please contact an administrator.", "warning")
            return redirect(url_for("main.dashboard"))

        start_date_str = request.form.get("start_date", "").strip()
        end_date_str = request.form.get("end_date", "").strip()
        reason = request.form.get("reason", "").strip()

        error = None
        start_date = end_date = None
        if not start_date_str or not end_date_str:
            error = "Start and end dates are required."
        else:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                if end_date < start_date:
                    raise ValueError
            except ValueError:
                error = "Please provide valid start and end dates (end date cannot be before start date)."

        if error:
            flash(error, "danger")
        else:
            leave_request = LeaveRequest(
                employee=employee,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
            )
            db.session.add(leave_request)
            db.session.commit()
            flash("Leave request submitted. We'll notify you once it's reviewed.", "success")
            return redirect(url_for("main.dashboard"))

    leave_requests = []
    if employee:
        leave_requests = (
            LeaveRequest.query.filter_by(employee_id=employee.id)
            .order_by(LeaveRequest.requested_at.desc())
            .all()
        )

    return render_template("profile.html", employee=employee, leave_requests=leave_requests)


@main_bp.route("/admin/manage", methods=["GET", "POST"])
@login_required
def manage():
    if not _current_user_is_admin():
        flash("Administrator privileges are required to access management tools.", "danger")
        return redirect(url_for("main.dashboard"))

    form_type = request.form.get("form_type")
    if request.method == "POST":
        if form_type == "create_user":
            _handle_user_creation()
        elif form_type == "create_employee":
            _handle_employee_creation()
        return redirect(url_for("main.manage"))

    users = User.query.order_by(User.username.asc()).all()
    employees = Employee.query.order_by(Employee.id.asc()).all()
    available_users = User.query.filter(User.employee_profile == None).order_by(User.username.asc()).all()  # noqa: E711
    return render_template(
        "manage.html",
        users=users,
        employees=employees,
        available_users=available_users,
    )


def _handle_user_creation() -> None:
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role = (request.form.get("role") or "user").strip() or "user"

    if not username or not password:
        flash("Username and password are required.", "danger")
        return

    if User.query.filter_by(username=username).first():
        flash("A user with that username already exists.", "warning")
        return

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f"User '{username}' created successfully.", "success")


def _handle_employee_creation() -> None:
    user_id = request.form.get("user_id")
    name = request.form.get("name", "").strip()
    role = request.form.get("employee_role", "").strip()
    salary = request.form.get("salary", "").strip()
    start_date_str = request.form.get("start_date", "").strip()
    leave_days_str = request.form.get("leave_days", "").strip()

    error = None
    if not user_id:
        error = "Please select a user to assign this employee profile."
    else:
        try:
            user_id = int(user_id)
        except ValueError:
            error = "Invalid user selection."

    user = None
    if not error:
        user = User.query.get(user_id)
        if not user:
            error = "Selected user could not be found."
        elif user.employee_profile:
            error = "This user already has an employee profile."

    if not name or not role or not salary:
        error = error or "All fields are required."

    start_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            error = error or "Start date must be a valid date."

    leave_days = 0
    if leave_days_str:
        try:
            leave_days = int(leave_days_str)
            if leave_days < 0:
                raise ValueError
        except ValueError:
            error = error or "Leave days must be a non-negative integer."

    try:
        salary_value = float(salary)
        if salary_value < 0:
            raise ValueError
    except (TypeError, ValueError):
        error = error or "Salary must be a positive number."

    if error:
        flash(error, "danger")
        return

    employee = Employee(
        user=user,
        name=name,
        role=role,
        salary=salary_value,
        start_date=start_date,
        leave_days=leave_days,
    )
    db.session.add(employee)
    db.session.commit()
    flash("Employee profile created successfully.", "success")


@main_bp.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id: int):
    if not _current_user_is_admin():
        flash("Administrator privileges are required to edit employees.", "danger")
        return redirect(url_for("main.dashboard"))

    employee = Employee.query.get_or_404(employee_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "").strip()
        salary = request.form.get("salary", "").strip()
        start_date_str = request.form.get("start_date", "").strip()
        leave_days_str = request.form.get("leave_days", "").strip()

        error = None
        if not name or not role or not salary:
            error = "All fields are required."

        start_date = employee.start_date
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                error = error or "Start date must be a valid date."

        leave_days = employee.leave_days
        if leave_days_str:
            try:
                leave_days = int(leave_days_str)
                if leave_days < 0:
                    raise ValueError
            except ValueError:
                error = error or "Leave days must be a non-negative integer."

        try:
            salary_value = float(salary)
            if salary_value < 0:
                raise ValueError
        except (TypeError, ValueError):
            error = error or "Salary must be a positive number."

        if error:
            flash(error, "danger")
        else:
            employee.name = name
            employee.role = role
            employee.salary = salary_value
            employee.start_date = start_date
            employee.leave_days = leave_days
            db.session.commit()
            flash("Employee updated successfully.", "success")
            return redirect(url_for("main.dashboard"))

    return render_template("edit.html", employee=employee)


@main_bp.route("/employees/<int:employee_id>/delete", methods=["POST"])
@login_required
def delete_employee(employee_id: int):
    if not _current_user_is_admin():
        flash("Administrator privileges are required to delete employees.", "danger")
        return redirect(url_for("main.dashboard"))

    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    flash("Employee deleted successfully.", "info")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/leave-requests/<int:request_id>/approve", methods=["POST"])
@login_required
def approve_leave_request(request_id: int):
    if not _current_user_is_admin():
        flash("Administrator privileges are required to approve leave requests.", "danger")
        return redirect(url_for("main.dashboard"))

    leave_request = LeaveRequest.query.get_or_404(request_id)
    if leave_request.status == "approved":
        flash("This leave request has already been approved.", "info")
    else:
        leave_request.status = "approved"
        leave_request.decided_at = datetime.utcnow()
        db.session.commit()
        flash("Leave request approved.", "success")
    return redirect(url_for("main.dashboard"))
