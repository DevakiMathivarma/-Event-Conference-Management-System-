from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin_or_organizer
from app.database import get_db
from app.models.user import User
from app.schemas.dashboard_schema import OrganizerDashboardResponse
from app.services.organizer_dashboard_service import get_organizer_dashboard

router = APIRouter(prefix="/api/v1/events", tags=["Organizer Dashboard"])


@router.get("/{event_id}/dashboard", response_model=OrganizerDashboardResponse)
def organizer_dashboard(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return get_organizer_dashboard(event_id, current_user, db)