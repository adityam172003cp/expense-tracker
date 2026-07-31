from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.expense import Expense
from app.models.sector import Sector
from app.schemas.dashboard import DashboardSectorItem, DashboardSummary
from app.services.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _month_range() -> tuple[date, date]:
    today = date.today()
    return today.replace(day=1), today


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
) -> DashboardSummary:
    first_of_month, today = _month_range()
    total_budget = (
        db.query(func.coalesce(func.sum(Sector.monthly_budget), 0))
        .filter(Sector.user_id == current_user.id, Sector.active.is_(True))
        .scalar()
    )
    total_spent = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.user_id == current_user.id,
            Expense.sector_id.in_(db.query(Sector.id).filter(Sector.user_id == current_user.id, Sector.active.is_(True))),
            Expense.date >= first_of_month,
            Expense.date <= today,
        )
        .scalar()
    )
    return DashboardSummary(
        total_budget=Decimal(total_budget),
        total_spent=Decimal(total_spent),
        total_remaining=max(Decimal(total_budget) - Decimal(total_spent), Decimal("0.00")),
        days_left_in_month=(today.replace(day=28) + date.resolution).day if today.day < 28 else 0,
    )


@router.get("/sectors", response_model=list[DashboardSectorItem])
def get_sector_summary(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
) -> list[DashboardSectorItem]:
    first_of_month, today = _month_range()
    sectors = (
        db.query(Sector)
        .filter(Sector.user_id == current_user.id, Sector.active.is_(True))
        .all()
    )
    sector_spent = {
        row.sector_id: row.spent
        for row in (
            db.query(
                Expense.sector_id,
                func.coalesce(func.sum(Expense.amount), 0).label("spent"),
            )
            .filter(
                Expense.user_id == current_user.id,
                Expense.date >= first_of_month,
                Expense.date <= today,
            )
            .group_by(Expense.sector_id)
            .all()
        )
    }

    result = []
    for sector in sectors:
        spent = Decimal(sector_spent.get(sector.id, 0))
        percent = (spent / sector.monthly_budget * 100) if sector.monthly_budget else Decimal("0")
        level = "ok"
        if percent >= 100:
            level = "exceeded"
        elif percent >= 90:
            level = "critical"
        elif percent >= 70:
            level = "warning"
        result.append(
            DashboardSectorItem(
                sector_id=sector.id,
                name=sector.name,
                monthly_budget=sector.monthly_budget,
                spent=spent,
                remaining=max(sector.monthly_budget - spent, Decimal("0.00")),
                percent_used=percent,
                alert_level=level,
                color_tag=sector.color_tag,
            )
        )
    return result
