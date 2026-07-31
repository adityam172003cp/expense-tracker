from datetime import date
from decimal import Decimal
from collections import defaultdict
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.expense import Expense
from app.models.sector import Sector
from app.schemas.analytics import (
    BreakdownItem,
    BudgetVsActualItem,
    HeatmapDay,
    MonthlyTrendItem,
    TrendPoint,
)
from app.services.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _month_range() -> tuple[date, date]:
    today = date.today()
    return today.replace(day=1), today


@router.get("/trend", response_model=list[TrendPoint])
def get_trend(
    range: str = Query("month"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TrendPoint]:
    first_of_month, today = _month_range()
    daily = [
        row
        for row in (
            db.query(
                Expense.date,
                func.coalesce(func.sum(Expense.amount), 0).label("spent"),
            )
            .filter(
                Expense.user_id == current_user.id,
                Expense.sector_id.in_(db.query(Sector.id).filter(Sector.user_id == current_user.id, Sector.active.is_(True))),
                Expense.date >= first_of_month,
                Expense.date <= today,
            )
            .group_by(Expense.date)
            .order_by(Expense.date)
            .all()
        )
    ]

    result = []
    cumulative = Decimal("0.00")
    days = (today - first_of_month).days + 1
    ideal_total = Decimal("0.00")
    for idx, row in enumerate(daily, start=1):
        cumulative += row.spent
        ideal_total = Decimal("0.00")
        if days > 0:
            ideal_total = cumulative / idx * days
        result.append(
            TrendPoint(date=row.date, actual_spend=row.spent, ideal_spend=ideal_total)
        )
    return result


@router.get("/breakdown", response_model=list[BreakdownItem])
def get_breakdown(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
) -> list[BreakdownItem]:
    first_of_month, today = _month_range()
    sector_totals = (
        db.query(
            Sector.id,
            Sector.name,
            func.coalesce(func.sum(Expense.amount), 0).label("spent"),
        )
        .join(Expense, Expense.sector_id == Sector.id)
        .filter(
            Sector.user_id == current_user.id,
            Sector.active.is_(True),
            Expense.date >= first_of_month,
            Expense.date <= today,
        )
        .group_by(Sector.id)
        .all()
    )

    total_spent = sum(row.spent for row in sector_totals)
    return [
        BreakdownItem(
            sector_id=row.id,
            name=row.name,
            spent=row.spent,
            share_percent=(row.spent / total_spent * 100) if total_spent else Decimal("0"),
        )
        for row in sector_totals
    ]


@router.get("/budget-vs-actual", response_model=list[BudgetVsActualItem])
def get_budget_vs_actual(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
) -> list[BudgetVsActualItem]:
    first_of_month, today = _month_range()
    sector_rows = (
        db.query(
            Sector.id,
            Sector.name,
            Sector.monthly_budget,
            func.coalesce(func.sum(Expense.amount), 0).label("spent"),
        )
        .outerjoin(Expense, Expense.sector_id == Sector.id)
        .filter(Sector.user_id == current_user.id, Sector.active.is_(True))
        .filter(Expense.date >= first_of_month, Expense.date <= today)
        .group_by(Sector.id)
        .all()
    )
    return [
        BudgetVsActualItem(
            sector_id=row.id,
            name=row.name,
            budget=row.monthly_budget,
            spent=row.spent,
            percent_used=(row.spent / row.monthly_budget * 100) if row.monthly_budget else Decimal("0"),
        )
        for row in sector_rows
    ]


@router.get("/heatmap", response_model=list[HeatmapDay])
def get_heatmap(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
) -> list[HeatmapDay]:
    first_of_month, today = _month_range()
    rows = (
        db.query(
            Expense.date,
            func.coalesce(func.sum(Expense.amount), 0).label("amount"),
        )
        .filter(
            Expense.user_id == current_user.id,
            Expense.sector_id.in_(db.query(Sector.id).filter(Sector.user_id == current_user.id, Sector.active.is_(True))),
            Expense.date >= first_of_month,
            Expense.date <= today,
        )
        .group_by(Expense.date)
        .order_by(Expense.date)
        .all()
    )
    return [HeatmapDay(date=row.date, amount=row.amount) for row in rows]


@router.get("/monthly-trend", response_model=list[MonthlyTrendItem])
def get_monthly_trend(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MonthlyTrendItem]:
    rows = (
        db.query(Expense.date, Expense.amount, Sector.id, Sector.name)
        .join(Sector, Expense.sector_id == Sector.id)
        .filter(Sector.user_id == current_user.id, Sector.active.is_(True))
        .all()
    )
    totals: defaultdict[tuple[str, int, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
    for expense_date, amount, sector_id, name in rows:
        totals[(expense_date.strftime("%Y-%m"), sector_id, name)] += amount
    return [
        MonthlyTrendItem(month=month, sector_id=sector_id, name=name, total_spent=total_spent)
        for (month, sector_id, name), total_spent in sorted(totals.items())
    ]
