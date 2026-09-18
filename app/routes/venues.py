from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin_or_organizer, require_any_role
from app.database import get_db
from app.models.user import User
from app.models.venue import VenueStatus
from app.schemas.hall_schema import HallCreate, HallMessageResponse, HallListResponse
from app.schemas.venue_schema import VenueCreate, VenueMessageResponse, VenuePaginationResponse
from app.services.hall_service import create_hall, get_halls_for_venue
from app.services.venue_service import create_venue, get_all_venues

router = APIRouter(prefix="/api/v1/venues", tags=["Venue & Hall Management"])


@router.post("", response_model=VenueMessageResponse, status_code=status.HTTP_201_CREATED)
def create_new_venue(data: VenueCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return create_venue(data, current_user, db)


@router.get("", response_model=VenuePaginationResponse, dependencies=[Depends(require_any_role)])
def list_venues(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    city: str | None = Query(None),
    status_filter: VenueStatus | None = Query(None, alias="status"),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_venues(db=db, page=page, limit=limit, city=city, status_filter=status_filter, search=search, sort_by=sort_by, sort_order=sort_order)


@router.post("/{venue_id}/halls", response_model=HallMessageResponse, status_code=status.HTTP_201_CREATED)
def create_new_hall(venue_id: int, data: HallCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return create_hall(venue_id, data, current_user, db)


@router.get("/{venue_id}/halls", response_model=HallListResponse, dependencies=[Depends(require_any_role)])
def list_halls(venue_id: int, db: Session = Depends(get_db)):

    return get_halls_for_venue(venue_id, db)