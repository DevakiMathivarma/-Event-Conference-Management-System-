from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_attendee, require_any_role
from app.database import get_db
from app.models.user import User
from app.schemas.feedback_schema import FeedbackCreate, FeedbackMessageResponse, FeedbackPaginationResponse
from app.services.feedback_service import create_feedback, get_all_feedback

router = APIRouter(prefix="/api/v1/feedback", tags=["Feedback Management"])


@router.post("", response_model=FeedbackMessageResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(data: FeedbackCreate, db: Session = Depends(get_db), current_user: User = Depends(require_attendee)):

    return create_feedback(data, current_user, db)


@router.get("", response_model=FeedbackPaginationResponse, dependencies=[Depends(require_any_role)])
def list_feedback(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    event_id: int | None = Query(None),
    speaker_id: int | None = Query(None),
    session_id: int | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_feedback(db=db, page=page, limit=limit, event_id=event_id, speaker_id=speaker_id, session_id=session_id, sort_by=sort_by, sort_order=sort_order)