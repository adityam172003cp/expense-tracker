from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel


class MonthlyReportItem(BaseModel):
    month: str
    total_spent: Decimal
    total_budget: Decimal
    summary: Optional[str] = None


class MonthlyReportDetail(BaseModel):
    month: str
    total_spent: Decimal
    total_budget: Decimal
    summary: Optional[str] = None
    details: Optional[Any] = None
