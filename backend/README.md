# Expense Tracker — Backend

This document describes how to run the FastAPI backend, database setup, migrations, seeding, and includes example API calls.

## Prerequisites

- Python 3.11+ (project uses venv at `backend/.venv`)
- MySQL server (or use SQLite for local quick testing and Docker)
- `mysql` user and an `expense_tracker` database (if using MySQL)

## Environment

Create a `.env` file in the `backend/` folder. Example:

```
DB_URL=mysql+pymysql://root:Adity%4098.321@localhost:3306/expense_tracker
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET=change-me-in-local-dev
VITE_API_BASE_URL=http://localhost:5173
```

Notes:
- If your DB password contains `@`, encode it as `%40` (see example above).
- For quick local testing you can omit `.env` and the app will use `sqlite:///./expense_tracker.db`.

## Setup (local)

Windows PowerShell example (run from project root):

```powershell
cd "c:\Education file\Expence tracker\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run with Docker

Docker Compose runs the backend and frontend together. From the project root:

```powershell
docker compose up --build
```

The backend is available at http://localhost:8000 and its interactive API docs are at http://localhost:8000/docs. The frontend is available at http://localhost:5173.

The Docker setup uses SQLite in a named `expense-data` volume and automatically applies Alembic migrations before starting FastAPI. The database remains available when containers are recreated. To stop the stack:

```powershell
docker compose down
```

To also delete the Docker database volume and start with an empty database:

```powershell
docker compose down -v
```

Optional settings can be provided through environment variables before starting the stack:

```powershell
$env:JWT_SECRET = "replace-with-a-long-secret"
$env:GROQ_API_KEY = "your_groq_api_key_here"
docker compose up --build
```

To seed sample data in the running backend container:

```powershell
docker compose exec backend python -m app.seed
```

## Database migrations

Initialize Alembic (already done in this repo). To apply migrations:

```powershell
cd "c:\Education file\Expence tracker\backend"
.\.venv\Scripts\Activate.ps1
python -m alembic upgrade head
```

If you switch to MySQL after previously using SQLite, ensure your `.env` `DB_URL` points to MySQL and re-run the migration above.

## Seed sample data

Run the seed script to create a test user and sample sectors/expenses:

```powershell
cd "c:\Education file\Expence tracker\backend"
.\.venv\Scripts\Activate.ps1
python -m app.seed
```

## Run the server

Start the FastAPI dev server:

```powershell
cd "c:\Education file\Expence tracker\backend"
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open the interactive docs at: http://127.0.0.1:8000/docs

## Example API usage (curl)

1) Register a user

```bash
curl -X POST "http://127.0.0.1:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Password123!","full_name":"Alice"}'
```

2) Login and get token

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Password123!"}'

# Response example:
# {"access_token":"<token>","token_type":"bearer"}
```

3) Create a sector (replace `<TOKEN>`)

```bash
curl -X POST "http://127.0.0.1:8000/sectors/" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Groceries","monthly_budget":450.00,"color_tag":"#4CAF50"}'
```

4) Add an expense

```bash
curl -X POST "http://127.0.0.1:8000/expenses/" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"sector_id":1,"amount":35.12,"note":"Weekly groceries","date":"2026-07-31"}'
```

5) Get dashboard summary

```bash
curl -X GET "http://127.0.0.1:8000/dashboard/summary" -H "Authorization: Bearer <TOKEN>"
```

## Migrations & Alembic notes

- Alembic config (`backend/migrations/env.py`) is set to read `DB_URL` from `backend/app/database.py` and will escape percent signs when required.

## Troubleshooting

- If you see Pydantic warnings about `orm_mode`, the project has been updated for Pydantic v2 (`from_attributes = True`) in schema files.
- If tables are not visible in MySQL Workbench: confirm your `DB_URL` in `backend/.env` points to `expense_tracker` on your MySQL instance and that migrations have been applied.
- If you hit bcrypt length issues, the project uses `pbkdf2_sha256` via Passlib to avoid the 72-byte bcrypt limit.

## Next steps

- Frontend expects API at `VITE_API_BASE_URL`, update `frontend/.env` or `VITE_API_BASE_URL` accordingly.
- To enable AI features set `GROQ_API_KEY` in `.env`.

---

File generated: `backend/README.md`
