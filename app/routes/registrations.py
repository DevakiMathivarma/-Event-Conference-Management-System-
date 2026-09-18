from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_attendee, require_any_role
from app.auth.current_user import get_current_user
from app.database import get_db
from app.models.registration import RegistrationStatus
from app.models.user import User
from app.schemas.registration_schema import RegistrationMessageResponse, RegistrationPaginationResponse
from app.services.registration_service import create_registration, get_registration_by_id, get_all_registrations, cancel_registration
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["Registration Management"])


@router.post("/events/{event_id}/register", response_model=RegistrationMessageResponse, status_code=status.HTTP_201_CREATED)
def register_for_event(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_attendee)):

    return create_registration(event_id, current_user, db)




@router.get("/registrations", response_model=RegistrationPaginationResponse, dependencies=[Depends(require_any_role)])
def list_registrations(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    event_id: int | None = Query(None),
    status_filter: RegistrationStatus | None = Query(None, alias="status"),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: Session = Depends(get_db)
):

    return get_all_registrations(db=db, page=page, limit=limit, event_id=event_id, status_filter=status_filter, start_date=start_date, end_date=end_date)


@router.get("/registrations/{registration_id}", response_model=RegistrationMessageResponse, dependencies=[Depends(require_any_role)])
def get_registration(registration_id: int, db: Session = Depends(get_db)):

    return get_registration_by_id(registration_id, db)


@router.post("/registrations/{registration_id}/cancel", response_model=RegistrationMessageResponse)
def cancel_existing_registration(registration_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return cancel_registration(registration_id, current_user, db)