from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.sector import Sector
from app.schemas.sector import SectorCreate, SectorOut, SectorUpdate
from app.services.dependencies import get_current_user
from app.database import get_db

router = APIRouter(prefix="/sectors", tags=["sectors"])


def _get_month_range() -> tuple[date, date]:
    today = date.today()
    first = today.replace(day=1)
    return first, today


def _apply_metrics(sector: Sector, spent: Decimal) -> Sector:
    sector.current_month_spent = spent
    sector.remaining_budget = max(sector.monthly_budget - spent, Decimal("0.00"))
    percent = (spent / sector.monthly_budget * 100) if sector.monthly_budget else Decimal("0")
    if percent >= 100:
        sector.alert_level = "exceeded"
    elif percent >= 90:
        sector.alert_level = "critical"
    elif percent >= 70:
        sector.alert_level = "warning"
    else:
        sector.alert_level = "ok"
    return sector


@router.post("/", response_model=SectorOut, status_code=status.HTTP_201_CREATED)
def create_sector(
    sector_in: SectorCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Sector:
    sector = Sector(
        user_id=current_user.id,
        name=sector_in.name,
        monthly_budget=sector_in.monthly_budget,
        color_tag=sector_in.color_tag,
    )
    db.add(sector)
    db.commit()
    db.refresh(sector)
    return _apply_metrics(sector, Decimal("0.00"))


@router.get("/", response_model=list[SectorOut])
def list_sectors(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Sector]:
    first_of_month, today = _get_month_range()
    expense_totals = (
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
        .subquery()
    )

    sectors = (
        db.query(Sector)
        .filter(Sector.user_id == current_user.id, Sector.active.is_(True))
        .all()
    )

    for sector in sectors:
        spent = Decimal("0.00")
        row = db.query(expense_totals).filter(expense_totals.c.sector_id == sector.id).first()
        if row is not None:
            spent = row.spent
        _apply_metrics(sector, spent)

    return sectors


@router.put("/{sector_id}", response_model=SectorOut)
def update_sector(
    sector_id: int,
    sector_in: SectorUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Sector:
    sector = (
        db.query(Sector)
        .filter(Sector.id == sector_id, Sector.user_id == current_user.id)
        .first()
    )
    if sector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sector not found")

    for field, value in sector_in.dict(exclude_unset=True).items():
        setattr(sector, field, value)
    db.commit()
    db.refresh(sector)
    first_of_month, today = _get_month_range()
    spent = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.user_id == current_user.id,
            Expense.sector_id == sector.id,
            Expense.date >= first_of_month,
            Expense.date <= today,
        )
        .scalar()
    )
    return _apply_metrics(sector, spent or Decimal("0.00"))


@router.delete("/{sector_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sector(
    sector_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    sector = (
        db.query(Sector)
        .filter(Sector.id == sector_id, Sector.user_id == current_user.id)
        .first()
    )
    if sector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sector not found")
    sector.active = False
    db.commit()
