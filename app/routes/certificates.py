from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin_or_organizer, require_any_role
from app.database import get_db
from app.models.user import User
from app.schemas.certificate_schema import CertificateGenerate, CertificateMessageResponse, CertificateListResponse
from app.services.certificate_service import generate_certificate, get_certificate_by_id, get_certificates_for_attendee

router = APIRouter(prefix="/api/v1", tags=["Certificate Management"])


@router.post("/certificates/generate/{registration_id}", response_model=CertificateMessageResponse, status_code=status.HTTP_201_CREATED)
def generate_new_certificate(registration_id: int, data: CertificateGenerate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return generate_certificate(registration_id, data, current_user, db)


@router.get("/certificates/{certificate_id}", response_model=CertificateMessageResponse, dependencies=[Depends(require_any_role)])
def get_certificate(certificate_id: int, db: Session = Depends(get_db)):

    return get_certificate_by_id(certificate_id, db)


@router.get("/attendees/{attendee_id}/certificates", response_model=CertificateListResponse, dependencies=[Depends(require_any_role)])
def list_attendee_certificates(attendee_id: int, db: Session = Depends(get_db)):

    return get_certificates_for_attendee(attendee_id, db)