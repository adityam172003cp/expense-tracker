from .auth import router as auth_router
from .ai import router as ai_router
from .analytics import router as analytics_router
from .expenses import router as expenses_router
from .reports import router as reports_router
from .sectors import router as sectors_router
from .dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "dashboard_router",
    "analytics_router",
    "ai_router",
    "expenses_router",
    "reports_router",
    "sectors_router",
]
