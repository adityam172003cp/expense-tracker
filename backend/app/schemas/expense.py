from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    sector_id: int
    amount: Decimal = Field(..., gt=0)
    note: Optional[str] = Field(None, max_length=512)
    date: date


class ExpenseOut(BaseModel):
    id: int
    sector_id: int
    amount: Decimal
    note: Optional[str] = None
    date: date
    created_at: datetime

    class Config:
        from_attributes = True
