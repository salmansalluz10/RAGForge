from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import DashboardStatsResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get aggregated metrics, processing breakdown, and recent activity for the dashboard.
    """
    return DashboardService.get_stats(db, current_user.id)
