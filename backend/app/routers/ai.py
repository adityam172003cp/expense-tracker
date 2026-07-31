from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.expense import Expense
from app.models.sector import Sector
from app.services.ai_service import AIService
from app.services.dependencies import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


class AITotals(BaseModel):
    period: str
    total_budget: str
    total_spent: str
    total_remaining: str


class AIInsightsResponse(BaseModel):
    insights: str
    totals: AITotals
    analysis: dict[str, object]


def _build_context(user_id: int, db: Session) -> dict[str, object]:
    today = date.today()
    month_start = today.replace(day=1)
    sectors = (
        db.query(Sector)
        .filter(Sector.user_id == user_id)
        .all()
    )
    expenses = (
        db.query(Expense)
        .filter(Expense.user_id == user_id, Expense.date >= month_start, Expense.date <= today)
        .order_by(Expense.date.desc())
        .limit(10)
        .all()
    )
    total_budget = db.query(func.coalesce(func.sum(Sector.monthly_budget), 0)).filter(Sector.user_id == user_id, Sector.active.is_(True)).scalar() or Decimal("0")
    active_sector_ids = db.query(Sector.id).filter(Sector.user_id == user_id, Sector.active.is_(True))
    total_spent = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(Expense.user_id == user_id, Expense.sector_id.in_(active_sector_ids), Expense.date >= month_start, Expense.date <= today).scalar() or Decimal("0")
    sector_spent = {
        row.sector_id: row.spent
        for row in db.query(Expense.sector_id, func.coalesce(func.sum(Expense.amount), 0).label("spent"))
        .filter(Expense.user_id == user_id, Expense.date >= month_start, Expense.date <= today)
        .group_by(Expense.sector_id)
        .all()
    }
    return {
        "period": today.strftime("%B %Y"),
        "total_budget": str(total_budget),
        "total_spent": str(total_spent),
        "total_remaining": str(max(Decimal(total_budget) - Decimal(total_spent), Decimal("0"))),
        "sectors": [{"id": s.id, "name": s.name, "budget": str(s.monthly_budget), "spent": str(sector_spent.get(s.id, 0))} for s in sectors if s.active],
        "recent_expenses": [
            {
                "id": e.id,
                "sector_id": e.sector_id,
                "amount": str(e.amount),
                "note": e.note,
                "date": str(e.date),
            }
            for e in expenses
        ],
    }


def _monthly_review(context: dict[str, object]) -> str:
    sectors = context["sectors"]
    total_spent = Decimal(context["total_spent"])
    total_budget = Decimal(context["total_budget"])
    active = [sector for sector in sectors if Decimal(sector["spent"]) > 0]
    ranked = sorted(sectors, key=lambda sector: Decimal(sector["spent"]), reverse=True)
    lines = [f"{context['period']} spending review", f"Total spent: INR {total_spent:,.2f} of INR {total_budget:,.2f} budget."]
    if ranked:
        lines.append("By sector: " + "; ".join(f"{sector['name']}: INR {Decimal(sector['spent']):,.2f} of INR {Decimal(sector['budget']):,.2f}" for sector in ranked))
        top = ranked[0]
        if Decimal(top["budget"]) and Decimal(top["spent"]) / Decimal(top["budget"]) >= Decimal("0.70"):
            lines.append(f"Warning: {top['name']} is using {Decimal(top['spent']) / Decimal(top['budget']) * 100:.0f}% of its budget. Reduce or pause non-essential spending there.")
        elif total_spent and Decimal(top["spent"]) / total_spent >= Decimal("0.50"):
            lines.append(f"Watch {top['name']}: it is your highest-spend sector this month. Compare non-essential purchases before spending more.")
    unused = [sector for sector in sectors if Decimal(sector["spent"]) == 0 and Decimal(sector["budget"]) > 0]
    if unused:
        lines.append("Underused budgets: " + ", ".join(sector["name"] for sector in unused) + ". Consider whether these planned priorities need funding this month.")
    health = [sector for sector in sectors if any(word in sector["name"].lower() for word in ("health", "diet", "fitness", "medical"))]
    if health and all(Decimal(sector["spent"]) == 0 for sector in health):
        lines.append("Health note: your health or diet budget has no spending yet. If this is a real priority, consider setting aside a small planned amount.")
    elif not health:
        lines.append("Priority check: there is no health or diet budget yet. If that matters to you, consider adding a modest planned budget rather than impulse spending.")
    lines.append("Save money by reviewing the highest-spend sector first; spend intentionally on planned priorities that are currently unused.")
    return "\n".join(lines)


def _build_analysis(context: dict[str, object]) -> dict[str, object]:
    sectors = context["sectors"]
    total_spent = Decimal(context["total_spent"])
    total_budget = Decimal(context["total_budget"])
    ranked = sorted(sectors, key=lambda sector: Decimal(sector["spent"]), reverse=True)
    sector_rows = []
    name_counts: dict[str, int] = {}
    for sector in ranked:
        name_counts[sector["name"]] = name_counts.get(sector["name"], 0) + 1
        display_name = sector["name"] if name_counts[sector["name"]] == 1 else f"{sector['name']} #{name_counts[sector['name']]}"
        budget = Decimal(sector["budget"])
        spent = Decimal(sector["spent"])
        percent = spent / budget * 100 if budget else Decimal("0")
        sector_rows.append({
            "name": display_name,
            "spent": str(spent),
            "budget": str(budget),
            "percent_used": str(percent.quantize(Decimal("0.1"))),
            "status": "over budget" if percent >= 100 else "high usage" if percent >= 70 else "on track" if spent else "unused",
        })
    top = ranked[0] if ranked else None
    warnings = []
    if top and Decimal(top["spent"]) > 0:
        top_budget = Decimal(top["budget"])
        top_percent = Decimal(top["spent"]) / top_budget * 100 if top_budget else Decimal("0")
        warnings.append(f"{top['name']} is your highest-spend sector at INR {Decimal(top['spent']):,.2f}.")
        if top_percent >= 70:
            warnings.append(f"{top['name']} has used {top_percent:.0f}% of its budget. Review non-essential purchases.")
    unused = [sector["name"] for sector in sectors if Decimal(sector["spent"]) == 0 and Decimal(sector["budget"]) > 0]
    save = [f"Review {top['name']} first and set a smaller limit for non-essential purchases." if top else "Add a few expenses so the app can identify your main saving opportunity."]
    spend = [f"Consider planned spending in: {', '.join(unused)}." if unused else "Keep spending aligned with your planned budgets."]
    health = [sector for sector in sectors if any(word in sector["name"].lower() for word in ("health", "diet", "fitness", "medical"))]
    if health and all(Decimal(sector["spent"]) == 0 for sector in health):
        spend.append("Your health or diet budget is unused; consider a modest planned allocation if it is a personal priority.")
    elif not health:
        spend.append("There is no health or diet budget. Add one only if it reflects a genuine personal priority.")
    return {
        "overview": f"You spent INR {total_spent:,.2f} of INR {total_budget:,.2f} this month, leaving INR {Decimal(context['total_remaining']):,.2f}.",
        "sector_breakdown": sector_rows,
        "warnings": warnings,
        "save_suggestions": save,
        "spend_suggestions": spend,
    }


@router.get("/insights")
def insights(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
) -> AIInsightsResponse:
    ai = AIService()
    context = _build_context(current_user.id, db)
    try:
        insights = ai.summarize_expenses(context)
    except Exception:
        raise HTTPException(status_code=503, detail="AI service unavailable")
    return AIInsightsResponse(
        insights=insights,
        totals=AITotals(**{key: context[key] for key in ("period", "total_budget", "total_spent", "total_remaining")}),
        analysis=_build_analysis(context),
    )


@router.post("/ask")
def ask(
    question: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    context = _build_context(current_user.id, db)
    normalized_question = question.lower()
    if any(word in normalized_question for word in ("expense", "expenses", "spending", "spent")) and ("month" in normalized_question or "how" in normalized_question or "review" in normalized_question):
        return {"answer": _monthly_review(context)}
    ai = AIService()
    try:
        answer = ai.ask(question, context)
    except Exception:
        raise HTTPException(status_code=503, detail="AI service unavailable")
    return {"answer": answer}
