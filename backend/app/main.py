import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    ai_router,
    analytics_router,
    auth_router,
    dashboard_router,
    expenses_router,
    reports_router,
    sectors_router,
)

app = FastAPI(title="Expense Tracker API")

origins = [
    os.getenv("VITE_API_BASE_URL", "http://localhost:5173"),
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(sectors_router)
app.include_router(expenses_router)
app.include_router(dashboard_router)
app.include_router(analytics_router)
app.include_router(ai_router)
app.include_router(reports_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Expense Tracker backend is running"}
