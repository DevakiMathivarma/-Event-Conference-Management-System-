from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin_or_organizer, require_any_role
from app.database import get_db
from app.models.event import EventStatus, EventType
from app.models.user import User
from app.schemas.common_schema import MessageResponse
from app.schemas.event_schema import EventCreate, EventUpdate, EventMessageResponse, EventPaginationResponse
from app.services.event_service import create_event, get_event_by_id, get_all_events, update_event, delete_event

router = APIRouter(prefix="/api/v1/events", tags=["Event Management"])


@router.post("", response_model=EventMessageResponse, status_code=status.HTTP_201_CREATED)
def create_new_event(data: EventCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return create_event(data, current_user, db)


@router.get("", response_model=EventPaginationResponse, dependencies=[Depends(require_any_role)])
def list_events(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    event_type: EventType | None = Query(None),
    city: str | None = Query(None),
    status_filter: EventStatus | None = Query(None, alias="status"),
    available_only: bool = Query(False),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_events(
        db=db, page=page, limit=limit, event_type=event_type, city=city, status_filter=status_filter, available_only=available_only,
        start_date=start_date, end_date=end_date, search=search, sort_by=sort_by, sort_order=sort_order
    )

@router.get("/{event_id}", response_model=EventMessageResponse, dependencies=[Depends(require_any_role)])
def get_event(event_id: int, db: Session = Depends(get_db)):

    return get_event_by_id(event_id, db)


@router.put("/{event_id}", response_model=EventMessageResponse)
def update_existing_event(event_id: int, data: EventUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return update_event(event_id, data, current_user, db)


@router.delete("/{event_id}", response_model=MessageResponse)
def remove_event(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return delete_event(event_id, current_user, db)