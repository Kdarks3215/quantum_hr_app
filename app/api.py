from datetime import datetime
from typing import Optional

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from . import db
from .models import Employee, User


api_bp = Blueprint("api", __name__)


def _get_requesting_user() -> Optional[User]:
    identity = get_jwt_identity()
    if identity is None:
        return None
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return None
    return User.query.get(user_id)


def _is_admin(user: Optional[User]) -> bool:
    return bool(user and (user.role or "").lower() == "admin")


@api_bp.get("/employees")
@jwt_required(optional=True)
def list_employees():
    requesting_user = _get_requesting_user()
    if requesting_user and not _is_admin(requesting_user):
        employee = Employee.query.filter_by(user_id=requesting_user.id).first()
        if not employee:
            return jsonify([])
        return jsonify([employee.as_dict()])

    employees = Employee.query.order_by(Employee.id.asc()).all()
    return jsonify([employee.as_dict() for employee in employees])


@api_bp.post("/employees")
@jwt_required()
def create_employee():
    requesting_user = _get_requesting_user()
    if not _is_admin(requesting_user):
        return jsonify({"message": "Administrator privileges required."}), 403

    data = request.get_json() or {}
    user_id = data.get("user_id")
    name = (data.get("name") or "").strip()
    role = (data.get("role") or "").strip()
    salary = data.get("salary")
    start_date_str = (data.get("start_date") or "").strip()
    leave_days_value = data.get("leave_days", 0)

    if not user_id or not isinstance(user_id, int):
        return jsonify({"message": "user_id is required and must be an integer."}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Referenced user does not exist."}), 404
    if user.employee_profile:
        return jsonify({"message": "User already has an employee profile."}), 400

    if not name or not role or salary is None or not start_date_str:
        return jsonify({"message": "name, role, salary, and start_date are required."}), 400

    try:
        salary_value = float(salary)
        if salary_value < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"message": "salary must be a positive number."}), 400

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "start_date must be in YYYY-MM-DD format."}), 400

    try:
        leave_days = int(leave_days_value)
        if leave_days < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"message": "leave_days must be a non-negative integer."}), 400

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
    return jsonify(employee.as_dict()), 201


@api_bp.put("/employees/<int:employee_id>")
@jwt_required()
def update_employee(employee_id: int):
    requesting_user = _get_requesting_user()
    if not _is_admin(requesting_user):
        return jsonify({"message": "Administrator privileges required."}), 403

    employee = Employee.query.get_or_404(employee_id)
    data = request.get_json() or {}

    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"message": "name cannot be empty."}), 400
        employee.name = name

    if "role" in data:
        role = (data.get("role") or "").strip()
        if not role:
            return jsonify({"message": "role cannot be empty."}), 400
        employee.role = role

    if "salary" in data:
        try:
            salary_value = float(data.get("salary"))
            if salary_value < 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"message": "salary must be a positive number."}), 400
        employee.salary = salary_value

    if "start_date" in data:
        start_date_str = (data.get("start_date") or "").strip()
        if not start_date_str:
            employee.start_date = None
        else:
            try:
                employee.start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"message": "start_date must be in YYYY-MM-DD format."}), 400

    if "leave_days" in data:
        try:
            leave_days_value = int(data.get("leave_days"))
            if leave_days_value < 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"message": "leave_days must be a non-negative integer."}), 400
        employee.leave_days = leave_days_value

    db.session.commit()
    return jsonify(employee.as_dict())


@api_bp.delete("/employees/<int:employee_id>")
@jwt_required()
def delete_employee(employee_id: int):
    requesting_user = _get_requesting_user()
    if not _is_admin(requesting_user):
        return jsonify({"message": "Administrator privileges required."}), 403

    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    return jsonify({"message": "Employee deleted."})
