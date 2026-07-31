# Expense Tracker — Implementation Plan

**Stack:** React (frontend) · FastAPI (backend) · MySQL (database) · Chart.js/Recharts (graphs) · Groq API (AI)

This plan breaks the build into sequential phases. Each phase has concrete tasks — work top to bottom, phase by phase. Check items off as you go.

---

## Phase 0 — Project Setup

- [ ] Create project root with two folders: `backend/` (FastAPI) and `frontend/` (React)
- [ ] Backend: set up a Python virtual environment, install `fastapi`, `uvicorn`, `sqlalchemy`, `pymysql`, `alembic`, `python-dotenv`, `pydantic`, `groq`, `apscheduler`, `passlib[bcrypt]`, `python-jose[cryptography]`
- [ ] Frontend: scaffold with `npm create vite@latest frontend -- --template react` (Vite is faster than CRA)
- [ ] Frontend: install `axios`, `react-router-dom`, `recharts` (or `chart.js` + `react-chartjs-2`), `bootstrap` or `tailwindcss` for styling, `react-toastify` for alerts
- [ ] Create MySQL database `expense_tracker` locally (MySQL Workbench / CLI)
- [ ] Set up `.env` files: backend (`DB_URL`, `GROQ_API_KEY`, `JWT_SECRET`), frontend (`VITE_API_BASE_URL`)
- [ ] Set up Git repo with a root `.gitignore` (node_modules, venv, .env, __pycache__)

---

## Phase 1 — Database Schema & Models

- [ ] Design tables in MySQL: `users`, `sectors`, `expenses`, `monthly_reports`, `budget_alerts` (as per the design doc's ER diagram)
- [ ] Write SQLAlchemy models for each table in `backend/app/models/`
- [ ] Set up Alembic for migrations (`alembic init migrations`)
- [ ] Write and run the first migration to create all tables
- [ ] Add seed script (`backend/app/seed.py`) to insert a test user and a few sample sectors for local development

---

## Phase 2 — FastAPI Core Setup

- [ ] Create `backend/app/main.py` with FastAPI app instance, CORS middleware (allow the Vite dev origin), and router registration
- [ ] Set up `backend/app/database.py` — SQLAlchemy engine, session, `get_db()` dependency
- [ ] Set up Pydantic schemas in `backend/app/schemas/` for request/response validation (`SectorCreate`, `SectorOut`, `ExpenseCreate`, etc.)
- [ ] Implement JWT-based auth: `POST /auth/register`, `POST /auth/login`, `get_current_user()` dependency
- [ ] Add global exception handlers for clean JSON error responses
- [ ] Verify server runs: `uvicorn app.main:app --reload` and `/docs` (Swagger UI) loads correctly

---

## Phase 3 — Sectors API

- [ ] `POST /sectors` — create a new sector (name, monthly_budget, color_tag)
- [ ] `GET /sectors` — list all sectors for the logged-in user, including current-month spend total per sector (via SQL aggregate join with expenses)
- [ ] `PUT /sectors/{id}` — update sector name/budget
- [ ] `DELETE /sectors/{id}` — delete sector (consider soft-delete/archive flag instead of hard delete, so historical charts survive)
- [ ] Write basic unit tests for sector CRUD (pytest + httpx TestClient)

---

## Phase 4 — Expenses API

- [ ] `POST /expenses` — add an expense (sector_id, amount, note, date); on save, recalculate sector's month-to-date total
- [ ] `GET /expenses?sector_id=&from=&to=` — list/filter expenses
- [ ] `DELETE /expenses/{id}` — remove an expense
- [ ] Add budget-check logic in the create-expense endpoint: compute % of budget used after this expense, return `alert_level` (`ok` / `warning` 70% / `critical` 90% / `exceeded` 100%+) in the response
- [ ] On `warning`/`critical`/`exceeded`, insert a row into `budget_alerts`
- [ ] Write tests for the alert threshold logic specifically (this is core to feature #12)

---

## Phase 5 — Dashboard & Analytics APIs

- [ ] `GET /dashboard/summary` — total budget, total spent, total remaining, days left in month (all sectors combined)
- [ ] `GET /dashboard/sectors` — per-sector spend vs. budget, % used, alert status (feeds the sector cards)
- [ ] `GET /analytics/trend?range=` — daily cumulative spend vs. ideal budget pace (for the line chart)
- [ ] `GET /analytics/breakdown` — spend share per sector this month (for the donut chart)
- [ ] `GET /analytics/budget-vs-actual` — per sector, for the bar chart
- [ ] `GET /analytics/heatmap` — daily spend intensity for the calendar heatmap
- [ ] `GET /analytics/monthly-trend` — month-over-month totals per sector

---

## Phase 6 — AI Integration (Groq)

- [ ] Create `backend/app/services/ai_service.py` — wraps the Groq client using your API token from `.env`
- [ ] Write a data-summarization helper that condenses recent expenses into a compact JSON payload (per-sector totals, trend deltas, top transactions) before sending to the AI — keeps prompts small and fast
- [ ] `GET /ai/insights` — returns 2–4 short real-time insights based on current-month data (called after new expenses are added, debounce/cache to avoid excessive API calls)
- [ ] `POST /ai/ask` — free-form question endpoint; passes user's question + spending summary as context to Groq
- [ ] Design and test the prompt template carefully — instruct the model to return structured JSON (insight text + severity) so the frontend can render consistently
- [ ] Handle Groq API errors/timeouts gracefully (fallback message if AI is unavailable)

---

## Phase 7 — Monthly Report Job

- [ ] Set up APScheduler in `backend/app/main.py` (or a separate worker) to run on the 1st of each month
- [ ] Write `generate_monthly_report(user_id)`: aggregate previous month's expenses per sector, compute totals/top sector/trend vs. prior month
- [ ] Send the aggregate to Groq with a prompt asking for: what went well, what to watch, and 3–5 concrete suggestions for next month
- [ ] Store the result in `monthly_reports`
- [ ] `GET /reports` — list past monthly reports
- [ ] `GET /reports/{month_year}` — full report detail
- [ ] `POST /reports/generate` — manual on-demand trigger (useful for testing without waiting for the 1st)

---

## Phase 8 — React Frontend: Foundation

- [ ] Set up routing (`react-router-dom`): `/login`, `/dashboard`, `/sectors`, `/analytics`, `/reports`
- [x] Create a typed API client with base URL + JWT interceptor (attach token, handle 401 → redirect to login)
- [x] Build shared layout: sidebar, responsive content container, and inline notifications
- [x] Build Login/Register flow, wire up to `/auth` endpoints, store JWT in localStorage
- [x] Set up local authenticated-user state for the frontend session

---

## Phase 9 — React Frontend: Dashboard & Sectors

- [x] Dashboard page: summary cards (total budget/spent/remaining/days left) fed by `/dashboard/summary`
- [x] Sector card grid: progress bar per sector (spent vs. budget), color-coded by alert status, "Add Expense" quick button
- [x] Sectors management page: table of sectors, new budget form, inline edit budget, archive with confirmation
- [ ] Add Expense modal: sector dropdown, amount, date picker, note field; show live remaining-budget preview as amount is typed; show inline warning if it will exceed budget
- [x] Wire real-time alert display: inline banner when API returns a budget warning condition

---

## Phase 10 — React Frontend: Analytics & Charts

- [ ] Donut chart — spend share by sector (Recharts `PieChart` or Chart.js)
- [ ] Line chart — daily cumulative spend vs. ideal pace line
- [ ] Bar chart — budget vs. actual per sector
- [ ] Calendar heatmap — daily spend intensity (e.g. `react-calendar-heatmap` or custom Recharts grid)
- [ ] Trend chart — month-over-month totals per sector
- [ ] Add date-range picker and sector filter controls shared across charts
- [ ] Make all charts interactive: tooltips on hover, click-to-filter, legend toggle

---

## Phase 11 — React Frontend: AI Insights & Reports

- [ ] AI Insights panel on the dashboard — fetches `/ai/insights`, renders as short cards/chat bubbles
- [ ] "Ask AI" free-form input box — calls `/ai/ask`, shows response inline
- [ ] Monthly Report page — fetch `/reports`, list past months; detail view shows totals, per-sector table, AI narrative, and next-month suggestions
- [ ] Add a "Generate now" button (dev/testing convenience, calls `/reports/generate`)
- [ ] Add print/export-to-PDF button on the report detail view (browser print CSS is enough for v1)

---

## Phase 12 — Polish & Hardening

- [ ] Responsive pass — verify dashboard, modals, and charts work well on mobile widths
- [ ] Add empty states (no sectors yet, no expenses yet, no report yet) and loading skeletons
- [ ] Form validation everywhere (amounts > 0, required fields, sane date ranges)
- [ ] Basic rate-limiting / caching around AI endpoints to control Groq usage
- [ ] Error boundaries in React; consistent error toasts from failed API calls
- [ ] Write a short `README.md` with setup instructions for both backend and frontend

---

## Phase 13 — Deployment

- [ ] Backend: containerize with Docker (`Dockerfile` for FastAPI + Uvicorn/Gunicorn); deploy to Railway/Render
- [ ] Database: managed MySQL (PlanetScale, Railway MySQL, or similar)
- [ ] Frontend: build with Vite (`npm run build`), deploy static bundle to Vercel/Netlify
- [ ] Set production environment variables (DB URL, JWT secret, Groq key) on the hosting platform — never commit secrets
- [ ] Point frontend's `VITE_API_BASE_URL` to the deployed backend URL
- [ ] Smoke-test the full flow in production: register → create sector → add expense → see alert → view charts → trigger report

---

## Suggested Order of Work (summary)

1. Phase 0–2: project scaffolding, DB, FastAPI core, auth
2. Phase 3–5: sectors, expenses, dashboard/analytics APIs (backend fully functional, testable via `/docs`)
3. Phase 6–7: AI insights + monthly report generation
4. Phase 8–11: React frontend, screen by screen, wired to the already-working backend
5. Phase 12–13: polish and deploy

This order lets you fully test and validate the backend (via FastAPI's built-in Swagger docs) before writing a single line of frontend code — reducing back-and-forth debugging later.
