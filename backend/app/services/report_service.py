import calendar
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.monthly_report import MonthlyReport
from app.models.sector import Sector
from app.models.user import User


def _year_month_for_date(target: date) -> str:
    return target.strftime("%Y-%m")


def generate_monthly_report(user_id: int, target_month: str, db: Session) -> MonthlyReport:
    year, month = map(int, target_month.split("-"))
    first_of_month = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last_of_month = date(year, month, last_day)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    sector_budgets = {
        sector.id: sector.monthly_budget
        for sector in db.query(Sector).filter(Sector.user_id == user_id, Sector.active.is_(True)).all()
    }

    expense_rows = (
        db.query(Expense.sector_id, func.coalesce(func.sum(Expense.amount), 0).label("spent"))
        .filter(
            Expense.user_id == user_id,
            Expense.date >= first_of_month,
            Expense.date <= last_of_month,
        )
        .group_by(Expense.sector_id)
        .all()
    )

    totals: dict[int, Decimal] = {sector_id: Decimal(spent) for sector_id, spent in expense_rows}
    total_spent = sum(totals.values(), Decimal("0.00"))
    total_budget = sum(sector_budgets.values(), Decimal("0.00"))

    sector_details: dict[str, Any] = {}
    for sector_id, budget in sector_budgets.items():
        spent = totals.get(sector_id, Decimal("0.00"))
        sector_details[str(sector_id)] = {
            "budget": str(budget),
            "spent": str(spent),
            "percent_used": str((spent / budget * 100) if budget else Decimal("0")),
        }

    previous_month = first_of_month.replace(day=1) - date.resolution
    previous_month_label = _year_month_for_date(previous_month)
    prev_total_spent = _sum_by_month(user_id, previous_month_label, db)
    delta = total_spent - prev_total_spent

    existing = (
        db.query(MonthlyReport)
        .filter(MonthlyReport.user_id == user_id, MonthlyReport.month == target_month)
        .first()
    )
    summary = (
        f"Your spending for {target_month} was {total_spent}. "
        f"Budget {total_budget}. "
        f"Change vs prior month: {delta:+}."
    )

    if existing:
        existing.total_spent = total_spent
        existing.total_budget = total_budget
        existing.summary = summary
        existing.details = {"sectors": sector_details, "delta": str(delta), "period": target_month}
        existing.created_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    report = MonthlyReport(
        user_id=user_id,
        month=target_month,
        total_spent=total_spent,
        total_budget=total_budget,
        summary=summary,
        details={"sectors": sector_details, "delta": str(delta), "period": target_month},
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def _sum_by_month(user_id: int, year_month: str, db: Session) -> Decimal:
    year, month = map(int, year_month.split("-"))
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    total = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.user_id == user_id,
            Expense.date >= first,
            Expense.date <= last,
        )
        .scalar()
    )
    return Decimal(total)
