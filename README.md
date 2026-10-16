# TaskFlow - Full-Stack Task Manager

A small full-stack app where users register, log in and manage their own tasks.
The backend is a REST API built with **FastAPI**, data is stored with **SQLAlchemy**
(SQLite locally, PostgreSQL in Docker), authentication uses **JWT**, and the frontend
is plain **HTML/CSS/JavaScript** served by the same server.

I built this project to learn how a real backend fits together: authentication,
password security, database relations, validation, authorization, tests and containers.

## Features

- Register and log in (JWT access token, 60 minute expiry)
- Passwords are hashed with **bcrypt** - plain passwords are never stored
- Create, list, update (mark done / edit) and delete tasks
- Filter tasks by status: `GET /tasks?done=true`
- **Per-user data isolation:** a user can never read or change another user's tasks
- Request validation with **Pydantic** (email format, password length, title length)
- Automated tests with **pytest** (5 tests, including the isolation rule)
- Interactive API docs at `/docs` (Swagger UI)
- Docker + Docker Compose setup with PostgreSQL

## Tech stack

| Layer | Technology |
|---|---|
| API | Python 3.12, FastAPI, Uvicorn |
| Database | SQLAlchemy 2 ORM, SQLite (dev) / PostgreSQL 16 (Docker) |
| Auth | JWT (PyJWT), bcrypt |
| Validation | Pydantic v2 |
| Frontend | HTML, CSS, vanilla JavaScript (`fetch`) |
| Tests | pytest, FastAPI TestClient |
| DevOps | Docker, Docker Compose |

## Architecture

```
Browser (frontend/index.html)
   |  fetch()  ->  Authorization: Bearer <token>
   v
FastAPI (app/main.py)
   |-- schemas.py   request / response validation (Pydantic)
   |-- security.py  password hashing + JWT create / verify
   |-- models.py    User 1 ---- * Task  (SQLAlchemy)
   v
Database (SQLite or PostgreSQL)
```

## Project structure

```
taskflow/
  app/
    main.py        API endpoints and auth dependency
    models.py      database tables (User, Task)
    schemas.py     Pydantic models for input / output
    security.py    bcrypt + JWT helpers
    database.py    engine, session, get_db dependency
  frontend/
    index.html     UI and JavaScript
  tests/
    test_api.py    pytest test suite
  Dockerfile
  docker-compose.yml
  requirements.txt
```

## Run locally (SQLite)

```bash
git clone https://github.com/ydvharsh01/taskflow.git
cd taskflow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 for the app and http://127.0.0.1:8000/docs for the API docs.

## Run with Docker (API + PostgreSQL)

```bash
docker compose up --build
```

Then open http://localhost:8000. Set your own secret first for anything beyond local use:

```bash
export SECRET_KEY=$(openssl rand -hex 32)
docker compose up --build
```

## Run the tests

```bash
pytest -q
```

## API endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | no | Create an account (`email`, `password`) |
| POST | `/auth/login` | no | Get a JWT token (form fields `username` = email, `password`) |
| GET | `/tasks` | yes | List my tasks, optional `?done=true/false` |
| POST | `/tasks` | yes | Create a task (`title`, optional `description`) |
| PATCH | `/tasks/{id}` | yes | Update `title`, `description` or `done` |
| DELETE | `/tasks/{id}` | yes | Delete a task |

Example:

```bash
curl -X POST localhost:8000/auth/register -H "Content-Type: application/json" \
  -d '{"email":"a@a.com","password":"secret123"}'
curl -X POST localhost:8000/auth/login -d "username=a@a.com&password=secret123"
curl localhost:8000/tasks -H "Authorization: Bearer <token>"
```

## Design decisions and security notes

- **bcrypt** with a random salt for passwords; login returns the same error for a wrong
  email and a wrong password so attackers cannot find out which emails are registered.
- **Ownership check on every task query.** Accessing someone else's task returns `404`
  (not `403`) so the existence of other users' tasks is not leaked. This is covered by a test.
- **SQLAlchemy ORM** uses parameterised queries, which protects against SQL injection.
- The frontend writes task titles with `textContent`, not `innerHTML`, to avoid XSS.
- `DATABASE_URL` and `SECRET_KEY` come from environment variables, so the same code
  runs with SQLite locally and PostgreSQL in Docker.

## Known limitations / next steps

- Tables are created at startup; add **Alembic** migrations for schema changes
- JWT is kept in `localStorage`; an `httpOnly` cookie plus refresh tokens would be safer
- Pagination for `GET /tasks`
- React version of the frontend
- GitHub Actions workflow to run the tests on every push

## Author

Harsh Yadav - [GitHub](https://github.com/ydvharsh01) | [LinkedIn](https://www.linkedin.com/in/harsh-yadav-013359367)
