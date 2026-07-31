from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from .base import Base


class AlertLevel(str, PyEnum):
    ok = "ok"
    warning = "warning"
    critical = "critical"
    exceeded = "exceeded"


class BudgetAlert(Base):
    __tablename__ = "budget_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sector_id = Column(Integer, ForeignKey("sectors.id", ondelete="SET NULL"), nullable=True, index=True)
    level = Column(String(32), nullable=False)
    message = Column(String(512), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    budget = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="budget_alerts")
