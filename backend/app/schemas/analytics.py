from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class TrendPoint(BaseModel):
    date: date
    actual_spend: Decimal
    ideal_spend: Decimal


class BreakdownItem(BaseModel):
    sector_id: int
    name: str
    spent: Decimal
    share_percent: Decimal


class BudgetVsActualItem(BaseModel):
    sector_id: int
    name: str
    budget: Decimal
    spent: Decimal
    percent_used: Decimal


class HeatmapDay(BaseModel):
    date: date
    amount: Decimal


class MonthlyTrendItem(BaseModel):
    month: str
    sector_id: int
    name: str
    total_spent: Decimal
