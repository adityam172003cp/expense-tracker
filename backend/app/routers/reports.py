from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.monthly_report import MonthlyReport
from app.schemas.report import MonthlyReportDetail, MonthlyReportItem
from app.services.dependencies import get_current_user
from app.services.report_service import generate_monthly_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/", response_model=list[MonthlyReportItem])
def list_reports(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MonthlyReportItem]:
    reports = (
        db.query(MonthlyReport)
        .filter(MonthlyReport.user_id == current_user.id)
        .order_by(MonthlyReport.month.desc())
        .all()
    )
    return [
        MonthlyReportItem(
            month=report.month,
            total_spent=report.total_spent,
            total_budget=report.total_budget,
            summary=report.summary,
        )
        for report in reports
    ]


@router.get("/{month_year}", response_model=MonthlyReportDetail)
def get_report(
    month_year: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MonthlyReportDetail:
    report = (
        db.query(MonthlyReport)
        .filter(MonthlyReport.user_id == current_user.id, MonthlyReport.month == month_year)
        .first()
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return MonthlyReportDetail(
        month=report.month,
        total_spent=report.total_spent,
        total_budget=report.total_budget,
        summary=report.summary,
        details=report.details,
    )


@router.post("/generate", response_model=MonthlyReportDetail)
def generate_report(
    month_year: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MonthlyReportDetail:
    report = generate_monthly_report(current_user.id, month_year, db)
    return MonthlyReportDetail(
        month=report.month,
        total_spent=report.total_spent,
        total_budget=report.total_budget,
        summary=report.summary,
        details=report.details,
    )
