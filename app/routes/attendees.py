from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.permissions import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.attendee_schema import AttendeeCreate, AttendeeUpdate, AttendeeMessageResponse, AttendeePaginationResponse
from app.services.attendee_service import create_attendee, get_attendee_by_id, get_all_attendees, update_attendee

router = APIRouter(prefix="/api/v1/attendees", tags=["Attendee Management"])


@router.post("", response_model=AttendeeMessageResponse, status_code=status.HTTP_201_CREATED)
def register_attendee(data: AttendeeCreate, db: Session = Depends(get_db)):

    return create_attendee(data, db)


@router.get("", response_model=AttendeePaginationResponse, dependencies=[Depends(require_admin)])
def list_attendees(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_attendees(db=db, page=page, limit=limit, search=search, sort_by=sort_by, sort_order=sort_order)


@router.get("/{attendee_id}", response_model=AttendeeMessageResponse)
def get_attendee(attendee_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return get_attendee_by_id(attendee_id, db)


@router.put("/{attendee_id}", response_model=AttendeeMessageResponse)
def update_existing_attendee(attendee_id: int, data: AttendeeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return update_attendee(attendee_id, data, current_user, db)