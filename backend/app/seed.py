from datetime import date

from app.database import engine
from app.models.base import Base
from app.models.budget_alert import BudgetAlert
from app.models.expense import Expense
from app.models.monthly_report import MonthlyReport
from app.models.sector import Sector
from app.models.user import User


def seed_data() -> None:
    Base.metadata.create_all(bind=engine)

    from sqlalchemy.orm import Session

    with Session(engine) as session:
        existing = session.query(User).filter(User.email == "test@example.com").first()
        if existing:
            print("Seed user already exists. Skipping seed data.")
            return

        user = User(email="test@example.com", password_hash="password", full_name="Sample User")
        session.add(user)
        session.flush()

        sectors = [
            Sector(user_id=user.id, name="Groceries", monthly_budget=450.00, color_tag="#4CAF50"),
            Sector(user_id=user.id, name="Utilities", monthly_budget=220.00, color_tag="#2196F3"),
            Sector(user_id=user.id, name="Entertainment", monthly_budget=180.00, color_tag="#FF9800"),
        ]
        session.add_all(sectors)
        session.commit()

        sample_expenses = [
            Expense(user_id=user.id, sector_id=sectors[0].id, amount=35.12, note="Weekly groceries", date=date.today()),
            Expense(user_id=user.id, sector_id=sectors[1].id, amount=85.50, note="Electricity bill", date=date.today()),
            Expense(user_id=user.id, sector_id=sectors[2].id, amount=42.75, note="Movie night", date=date.today()),
        ]
        session.add_all(sample_expenses)
        session.commit()
        print("Seed data created successfully.")


if __name__ == "__main__":
    seed_data()
