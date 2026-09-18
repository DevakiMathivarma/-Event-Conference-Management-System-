from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.permissions import require_event_staff_side
from app.database import get_db
from app.models.user import User
from app.schemas.check_in_schema import CheckInRequest, CheckInMessageResponse, AttendanceListResponse, QRVerificationResult
from app.services.check_in_service import check_in_registration, check_out_registration, verify_qr_check_in, get_event_attendance

router = APIRouter(prefix="/api/v1", tags=["Event Check-In"])


@router.post("/registrations/{registration_id}/check-in", response_model=CheckInMessageResponse, dependencies=[Depends(require_event_staff_side)])
def check_in(registration_id: int, data: CheckInRequest, db: Session = Depends(get_db), current_user: User = Depends(require_event_staff_side)):

    return check_in_registration(registration_id, data, current_user, db)


@router.post("/registrations/{registration_id}/check-out", response_model=CheckInMessageResponse, dependencies=[Depends(require_event_staff_side)])
def check_out(registration_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_event_staff_side)):

    return check_out_registration(registration_id, current_user, db)


@router.get("/events/{event_id}/attendance", response_model=AttendanceListResponse, dependencies=[Depends(get_current_user)])
def get_attendance(event_id: int, db: Session = Depends(get_db)):

    return get_event_attendance(event_id, db)


# the real qr-scanning endpoint we designed - accepts an uploaded image,
# not json, same pattern as property's visitor qr verification
@router.post("/check-in/verify-qr", response_model=QRVerificationResult, dependencies=[Depends(require_event_staff_side)])
async def verify_qr(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(require_event_staff_side)):

    image_bytes = await file.read()

    return verify_qr_check_in(image_bytes, current_user, db)

from app.schemas.dashboard_schema import AttendanceReportResponse
from app.services.check_in_service import get_attendance_report

@router.get("/events/{event_id}/attendance-report", response_model=AttendanceReportResponse, dependencies=[Depends(require_event_staff_side)])
def attendance_report(event_id: int, db: Session = Depends(get_db)):
    return get_attendance_report(event_id, db)