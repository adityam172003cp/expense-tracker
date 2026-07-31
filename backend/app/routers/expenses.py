from datetime import date
from decimal import Decimal

typing = None

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.budget_alert import BudgetAlert
from app.models.expense import Expense
from app.models.sector import Sector
from app.schemas.expense import ExpenseCreate, ExpenseOut
from app.services.dependencies import get_current_user
from app.database import get_db

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _alert_level_for_percent(percent: Decimal) -> str:
    if percent >= 100:
        return "exceeded"
    if percent >= 90:
        return "critical"
    if percent >= 70:
        return "warning"
    return "ok"


@router.post("/", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_in: ExpenseCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Expense:
    sector = (
        db.query(Sector)
        .filter(Sector.id == expense_in.sector_id, Sector.user_id == current_user.id)
        .first()
    )
    if sector is None or not sector.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sector not found")

    expense = Expense(
        user_id=current_user.id,
        sector_id=sector.id,
        amount=expense_in.amount,
        note=expense_in.note,
        date=expense_in.date,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    month_start = expense.date.replace(day=1)
    month_end = expense.date
    total_spent = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.user_id == current_user.id,
            Expense.sector_id == sector.id,
            Expense.date >= month_start,
            Expense.date <= month_end,
        )
        .scalar()
    )
    percent = (total_spent / sector.monthly_budget * 100) if sector.monthly_budget else Decimal("0")
    level = _alert_level_for_percent(percent)
    if level != "ok":
        alert = BudgetAlert(
            user_id=current_user.id,
            sector_id=sector.id,
            level=level,
            message=f"Budget {level}: {total_spent} of {sector.monthly_budget}",
            amount=total_spent,
            budget=sector.monthly_budget,
        )
        db.add(alert)
        db.commit()

    return expense


@router.get("/", response_model=list[ExpenseOut])
def list_expenses(
    sector_id: int | None = Query(None),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Expense]:
    query = db.query(Expense).filter(Expense.user_id == current_user.id)
    if sector_id is not None:
        query = query.filter(Expense.sector_id == sector_id)
    if from_date is not None:
        query = query.filter(Expense.date >= from_date)
    if to_date is not None:
        query = query.filter(Expense.date <= to_date)
    return query.order_by(Expense.date.desc()).all()


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.user_id == current_user.id)
        .first()
    )
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    db.delete(expense)
    db.commit()
