from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.registration import Registration, RegistrationStatus
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.check_in_repository import CheckInRepository
from app.schemas.check_in_schema import CheckInRequest
from app.utils.logger import logger
from app.utils.qr_code import decode_qr_code
from app.models.check_in import CheckIn 

def _perform_check_in(registration_id: int, check_in_method, current_user, db: Session):

    registration_repo = BaseRepository(Registration, db)
    checkin_repo = CheckInRepository(db)
    audit_repo = AuditLogRepository(db)

    registration = registration_repo.get_by_id(registration_id)

    if not registration:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found.")

    if registration.registration_status != RegistrationStatus.CONFIRMED:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only confirmed registrations can check in.")

    check_in = checkin_repo.get_by_registration_id(registration_id)

    if not check_in:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No check-in record exists for this registration.")

    if check_in.check_in_time is not None:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This attendee has already checked in.")

    check_in.check_in_time = datetime.now(timezone.utc)
    check_in.check_in_method = check_in_method
    check_in.checked_in_by_user_id = current_user.id

    audit_repo.log(
        user_id=current_user.id,
        action="CHECK_IN",
        entity_type="CheckIn",
        entity_id=check_in.id,
        description=f"Checked in via {check_in_method.value}"
    )

    db.commit()

    db.refresh(check_in)

    # bonus - live check-in count update, pushed to anyone watching
    # this event's check-in desk right now
    from app.routes.websocket import broadcast_check_in_update_sync

    total_checked_in = db.query(CheckIn).join(Registration, CheckIn.registration_id == Registration.id).filter(
        Registration.event_id == registration.event_id, CheckIn.check_in_time.isnot(None)
    ).count()

    broadcast_check_in_update_sync(registration.event_id, {
        "event_id": registration.event_id,
        "attendee_name": registration.attendee.user.full_name,
        "check_in_method": check_in_method.value,
        "total_checked_in": total_checked_in
    })

    return check_in

def check_in_registration(registration_id: int, data: CheckInRequest, current_user, db: Session) -> dict:

    try:

        logger.info(f"Checking in registration : {registration_id}, method {data.check_in_method.value}")

        check_in = _perform_check_in(registration_id, data.check_in_method, current_user, db)

        logger.info(f"Check-in successful : registration {registration_id}")

        return {"message": "Checked in successfully.", "data": check_in}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Check-in failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to check in.")


def check_out_registration(registration_id: int, current_user, db: Session) -> dict:

    try:

        logger.info(f"Checking out registration : {registration_id}")

        checkin_repo = CheckInRepository(db)
        audit_repo = AuditLogRepository(db)

        check_in = checkin_repo.get_by_registration_id(registration_id)

        if not check_in:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No check-in record exists for this registration.")

        if check_in.check_in_time is None:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This attendee has not checked in yet.")

        check_in.check_out_time = datetime.now(timezone.utc)

        audit_repo.log(
            user_id=current_user.id,
            action="CHECK_OUT",
            entity_type="CheckIn",
            entity_id=check_in.id,
            description="Checked out"
        )

        db.commit()

        db.refresh(check_in)

        logger.info(f"Check-out successful : registration {registration_id}")

        return {"message": "Checked out successfully.", "data": check_in}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Check-out failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to check out.")


def verify_qr_check_in(image_bytes: bytes, current_user, db: Session) -> dict:

    from app.models.check_in import CheckInMethod

    decoded_text = decode_qr_code(image_bytes)

    if not decoded_text or not decoded_text.startswith("REGISTRATION-"):

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not read a valid registration QR code from this image.")

    try:

        registration_id = int(decoded_text.replace("REGISTRATION-", ""))

    except ValueError:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid QR code content.")

    registration_repo = BaseRepository(Registration, db)

    registration = registration_repo.get_by_id(registration_id)

    if not registration:

        return {
            "registration_id": registration_id,
            "attendee_name": "Unknown",
            "event_name": "Unknown",
            "is_valid": False,
            "message": "No registration matches this QR code."
        }

    if registration.registration_status != RegistrationStatus.CONFIRMED:

        return {
            "registration_id": registration.id,
            "attendee_name": registration.attendee.user.full_name,
            "event_name": registration.event.event_name,
            "is_valid": False,
            "message": "This registration is not currently confirmed."
        }

    try:

        _perform_check_in(registration_id, CheckInMethod.QR_CODE, current_user, db)

        return {
            "registration_id": registration.id,
            "attendee_name": registration.attendee.user.full_name,
            "event_name": registration.event.event_name,
            "is_valid": True,
            "message": "QR code verified. Attendee checked in."
        }

    except HTTPException as error:

        return {
            "registration_id": registration.id,
            "attendee_name": registration.attendee.user.full_name,
            "event_name": registration.event.event_name,
            "is_valid": False,
            "message": error.detail
        }


def get_event_attendance(event_id: int, db: Session) -> dict:

    checkin_repo = CheckInRepository(db)

    check_ins = checkin_repo.list_for_event(event_id)

    return {"message": "Attendance fetched successfully.", "data": check_ins}

def get_attendance_report(event_id: int, db: Session) -> dict:

    checkin_repo = CheckInRepository(db)

    check_ins = checkin_repo.list_for_event(event_id)

    from app.schemas.dashboard_schema import AttendanceReportEntry

    data = [
        AttendanceReportEntry(
            attendee_name=c.registration.attendee.user.full_name,
            check_in_time=str(c.check_in_time) if c.check_in_time else None,
            check_out_time=str(c.check_out_time) if c.check_out_time else None,
            check_in_method=c.check_in_method.value if c.check_in_method else None
        )
        for c in check_ins
    ]

    return {"message": "Attendance report generated successfully.", "data": data}