# Quantum HR

Quantum HR is a full-stack employee management platform built with Flask and a modern Bootstrap UI. It supports session-based authentication for the web portal, JWT-protected REST APIs, employee record management, and leave request workflows.

## Features

- User authentication via Flask-Login and JWT tokens for API consumers
- Role-based controls with admin dashboards and employee self-service profile view
- Employee directory including salary in Ghana cedis, start date, and leave balances
- Leave request submission, tracking, and admin approvals
- Responsive UI styled with Bootstrap and custom glassmorphism accents
- Pytest suite covering registration, login, and authenticated CRUD flows
- Dockerfile and docker-compose configuration for containerized deployments
- Optional default data seeding on startup (configurable via `SEED_DEFAULT_DATA`)

## Getting Started

```bash
python -m venv venv
venv\Scripts\activate
pip install -r app/requirements.txt
flask run
```

Run tests:

```bash
python -m pytest
```

## Container Usage

```bash
docker compose up --build
```

By default the container seeds sample users (`admin`, `kwame`, `ama`, `yaw`, `efua`). Disable by setting `SEED_DEFAULT_DATA=false`.
