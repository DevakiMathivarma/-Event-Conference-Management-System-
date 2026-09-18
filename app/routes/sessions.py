from fastapi import APIRouter, Depends, status,Query
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin_or_organizer, require_any_role,get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.common_schema import MessageResponse
from app.schemas.session_schema import SessionCreate, SessionUpdate, SessionMessageResponse, SessionPaginationResponse
from app.services.session_service import create_session, get_sessions_for_event, get_session_by_id, update_session, delete_session

router = APIRouter(prefix="/api/v1", tags=["Session Management"])


@router.post("/sessions", response_model=SessionMessageResponse, status_code=status.HTTP_201_CREATED)
def create_new_session(data: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return create_session(data, current_user, db)


from datetime import date

@router.get("/events/{event_id}/sessions", response_model=SessionPaginationResponse, dependencies=[Depends(require_any_role)])
def list_event_sessions(
    event_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    speaker_id: int | None = Query(None),
    session_type: str | None = Query(None),
    date_filter: date | None = Query(None, alias="date"),
    sort_by: str = Query("start_time"),
    sort_order: str = Query("asc"),
    db: Session = Depends(get_db)
):

    return get_sessions_for_event(db=db, page=page, limit=limit, event_id=event_id, speaker_id=speaker_id, session_type=session_type, date_filter=date_filter, sort_by=sort_by, sort_order=sort_order)


@router.get("/sessions/{session_id}", response_model=SessionMessageResponse, dependencies=[Depends(require_any_role)])
def get_session(session_id: int, db: Session = Depends(get_db)):

    return get_session_by_id(session_id, db)


@router.put("/sessions/{session_id}", response_model=SessionMessageResponse)
def update_existing_session(session_id: int, data: SessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return update_session(session_id, data, current_user, db)


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
def remove_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return delete_session(session_id, current_user, db)

from app.auth.permissions import require_attendee
from app.schemas.session_booking_schema import SessionBookingMessageResponse, SessionBookingListResponse
from app.schemas.common_schema import MessageResponse
from app.services.session_booking_service import create_session_booking, get_sessions_for_attendee, delete_session_booking


@router.post("/sessions/{session_id}/book", response_model=SessionBookingMessageResponse, status_code=status.HTTP_201_CREATED)
def book_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_attendee)):

    return create_session_booking(session_id, current_user, db)


@router.get("/attendees/{attendee_id}/sessions", response_model=SessionBookingListResponse, dependencies=[Depends(require_any_role)])
def list_attendee_sessions(attendee_id: int, db: Session = Depends(get_db)):

    return get_sessions_for_attendee(attendee_id, db)


@router.delete("/session-bookings/{booking_id}", response_model=MessageResponse)
def cancel_session_booking(booking_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return delete_session_booking(booking_id, current_user, db)