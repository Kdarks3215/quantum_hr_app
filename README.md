# Quantum HR

Quantum HR is a full-stack employee management platform built with Flask and a modern Bootstrap UI. It supports session-based authentication for the web portal, JWT-protected REST APIs, employee record management, and leave request workflows.

## Features

- User authentication via Flask-Login and JWT tokens for API consumers
- Role-based controls with admin dashboards and employee self-service profile view
- Employee directory including salary in Ghana cedis, start date, and leave balances
- Leave request submission, approval, and rejection with manager comments
- Responsive UI styled with Bootstrap and custom glassmorphism accents
- Pytest suite covering registration, login, and authenticated CRUD flows
- Alembic-powered migrations for managing schema changes across environments
- Dockerfile and docker-compose configuration tuned for production (Gunicorn + Postgres)

## Configuration

Set the following environment variables for production deployments:

- `DATABASE_URL` – SQLAlchemy connection string (e.g. `postgresql+psycopg2://user:pass@host:5432/dbname`)
- `SECRET_KEY` – Flask session key
- `JWT_SECRET_KEY` – JWT signing secret
- `SEED_DEFAULT_DATA` – optional (`true`/`false`), seeds sample users when true

If `DATABASE_URL` is not provided the app falls back to `sqlite:///employees.db`, suitable only for local development.

## Local Development

```bash
python -m venv venv
venv\Scripts\activate
pip install -r app/requirements.txt
set DATABASE_URL=sqlite:///employees.db
alembic upgrade head
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

The compose file provisions Postgres and runs database migrations automatically on startup. Default sample users (`admin`, `kwame`, `ama`, `yaw`, `efua`) are seeded when `SEED_DEFAULT_DATA=true`.

## Alembic Workflow

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Remember to set `DATABASE_URL` in your environment before running Alembic commands so it targets the correct database.
