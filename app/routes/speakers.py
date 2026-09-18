from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin_or_organizer, require_any_role
from app.database import get_db
from app.models.user import User
from app.schemas.speaker_schema import SpeakerCreate, SpeakerUpdate, SpeakerMessageResponse, SpeakerPaginationResponse
from app.services.speaker_service import create_speaker, get_speaker_by_id, get_all_speakers, update_speaker

router = APIRouter(prefix="/api/v1/speakers", tags=["Speaker Management"])


@router.post("", response_model=SpeakerMessageResponse, status_code=status.HTTP_201_CREATED)
def create_new_speaker(data: SpeakerCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return create_speaker(data, current_user, db)


@router.get("", response_model=SpeakerPaginationResponse, dependencies=[Depends(require_any_role)])
def list_speakers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    expertise: str | None = Query(None),
    active_only: bool = Query(False),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_speakers(db=db, page=page, limit=limit, expertise=expertise, active_only=active_only, search=search, sort_by=sort_by, sort_order=sort_order)


@router.get("/{speaker_id}", response_model=SpeakerMessageResponse, dependencies=[Depends(require_any_role)])
def get_speaker(speaker_id: int, db: Session = Depends(get_db)):

    return get_speaker_by_id(speaker_id, db)


@router.put("/{speaker_id}", response_model=SpeakerMessageResponse)
def update_existing_speaker(speaker_id: int, data: SpeakerUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return update_speaker(speaker_id, data, current_user, db)