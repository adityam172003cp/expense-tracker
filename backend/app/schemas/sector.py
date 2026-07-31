from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class SectorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    monthly_budget: Decimal = Field(..., ge=0)
    color_tag: Optional[str] = Field(None, max_length=32)


class SectorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    monthly_budget: Optional[Decimal] = Field(None, ge=0)
    color_tag: Optional[str] = Field(None, max_length=32)
    active: Optional[bool] = None


class SectorOut(BaseModel):
    id: int
    name: str
    monthly_budget: Decimal
    color_tag: Optional[str] = None
    active: bool
    created_at: datetime
    current_month_spent: Decimal
    remaining_budget: Decimal
    alert_level: str

    class Config:
        from_attributes = True
