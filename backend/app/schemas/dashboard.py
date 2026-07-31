from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_budget: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    days_left_in_month: int


class DashboardSectorItem(BaseModel):
    sector_id: int
    name: str
    monthly_budget: Decimal
    spent: Decimal
    remaining: Decimal
    percent_used: Decimal
    alert_level: str
    color_tag: Optional[str] = None

    class Config:
        from_attributes = True
