from datetime import date

from . import db
from .models import Employee, User


def seed_defaults() -> None:
    default_entries = [
        {
            "username": "admin",
            "password": "admin",
            "role": "admin",
            "employee": {
                "name": "Admin User",
                "role": "Operations Manager",
                "salary": 12000.0,
                "start_date": date(2022, 1, 1),
                "leave_days": 25,
            },
        },
        {
            "username": "kwame",
            "password": "password123",
            "role": "user",
            "employee": {
                "name": "Kwame Mensah",
                "role": "Senior Stylist",
                "salary": 7200.0,
                "start_date": date(2023, 6, 1),
                "leave_days": 18,
            },
        },
        {
            "username": "ama",
            "password": "password123",
            "role": "user",
            "employee": {
                "name": "Ama Osei",
                "role": "Color Specialist",
                "salary": 6800.0,
                "start_date": date(2024, 2, 12),
                "leave_days": 15,
            },
        },
        {
            "username": "yaw",
            "password": "password123",
            "role": "user",
            "employee": {
                "name": "Yaw Owusu",
                "role": "Barber",
                "salary": 5400.0,
                "start_date": date(2023, 9, 5),
                "leave_days": 12,
            },
        },
        {
            "username": "efua",
            "password": "password123",
            "role": "user",
            "employee": {
                "name": "Efua Arko",
                "role": "Reception Lead",
                "salary": 4800.0,
                "start_date": date(2024, 5, 20),
                "leave_days": 20,
            },
        },
    ]

    for entry in default_entries:
        user = User.query.filter_by(username=entry["username"]).first()
        if not user:
            user = User(username=entry["username"], role=entry["role"])
            db.session.add(user)
        else:
            user.role = entry["role"]
        user.set_password(entry["password"])
        db.session.flush()

        employee_data = entry.get("employee")
        if not employee_data:
            continue

        employee = Employee.query.filter_by(user_id=user.id).first()
        if not employee:
            employee = Employee(user=user)
            db.session.add(employee)

        employee.name = employee_data["name"]
        employee.role = employee_data["role"]
        employee.salary = employee_data["salary"]
        employee.start_date = employee_data["start_date"]
        employee.leave_days = employee_data["leave_days"]

    db.session.commit()
