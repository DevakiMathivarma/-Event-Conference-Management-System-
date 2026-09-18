from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.check_in import CheckIn
from app.models.event import Event, EventStatus
from app.models.registration import Registration, RegistrationStatus
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.registration_repository import RegistrationRepository
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_registration(event_id: int, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating registration : attendee {current_user.attendee.id}, event {event_id}")

        event_repo = BaseRepository(Event, db)
        registration_repo = RegistrationRepository(db)
        audit_repo = AuditLogRepository(db)

        event = event_repo.get_by_id(event_id)

        if not event:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

        # cancelled events cannot accept registrations - level 2 business rule
        if event.status == EventStatus.CANCELLED:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This event has been cancelled and is no longer accepting registrations.")

        # registration is allowed only during the registration period -
        # level 6 business rule
        now = datetime.now(timezone.utc)

        reg_start = event.registration_start if event.registration_start.tzinfo else event.registration_start.replace(tzinfo=timezone.utc)
        reg_end = event.registration_end if event.registration_end.tzinfo else event.registration_end.replace(tzinfo=timezone.utc)

        if now < reg_start or now > reg_end:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration is not currently open for this event.")

        # prevent duplicate registration - friendly pre-check, backed
        # by the database's own unique constraint
        existing = registration_repo.get_by_attendee_and_event(current_user.attendee.id, event_id)

        if existing:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already registered for this event.")

        # registration cannot exceed event capacity - level 6 business rule
        confirmed_count = registration_repo.count_confirmed_for_event(event_id)

        if confirmed_count >= event.capacity:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This event has reached its registration capacity.")

        registration = Registration(
            attendee_id=current_user.attendee.id,
            event_id=event_id,
            registration_status=RegistrationStatus.PENDING
        )

        registration_repo.add(registration)

        db.flush()

        # a check-in record is created right away, in a "not yet
        # checked in" state - matching the model design we settled on,
        # where checking in updates this existing row rather than
        # inserting a new one
        db.add(CheckIn(registration_id=registration.id))

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Registration",
            entity_id=registration.id,
            description=f"Registered for event {event_id}"
        )

        db.commit()

        registration = registration_repo.get_by_id_with_details(registration.id)

        # level 13-equivalent notification - registration confirmation,
        # wired in immediately
        from app.tasks import send_registration_confirmation_email

        attendee_user = current_user

        send_registration_confirmation_email.delay(attendee_user.email, attendee_user.full_name, event.event_name)

        logger.info(f"Registration created successfully : {registration.id}")

        return {"message": "Registered successfully.", "data": registration}

    except HTTPException:

        raise

    except IntegrityError:

        db.rollback()

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already registered for this event.")

    except Exception as error:

        db.rollback()

        logger.error(f"Registration creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to register.")


def get_registration_by_id(registration_id: int, db: Session) -> dict:

    registration_repo = RegistrationRepository(db)

    registration = registration_repo.get_by_id_with_details(registration_id)

    if not registration:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found.")

    return {"message": "Registration fetched successfully.", "data": registration}


def get_all_registrations(db: Session, page: int = 1, limit: int = 10, event_id=None, status_filter=None, start_date=None, end_date=None, sort_by: str = "registration_date", sort_order: str = "desc") -> dict:

    logger.info("Fetching registrations list.")

    registration_repo = RegistrationRepository(db)

    sortable_columns = {"registration_date": Registration.registration_date}

    sort_column = sortable_columns.get(sort_by, Registration.registration_date)

    registrations, total_records = registration_repo.list_registrations(event_id, status_filter, start_date, end_date, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Registrations fetched successfully.", "data": registrations, "pagination": get_pagination(total_records, page, limit)}

def cancel_registration(registration_id: int, current_user, db: Session) -> dict:

    try:

        logger.info(f"Cancelling registration : {registration_id}")

        registration_repo = RegistrationRepository(db)
        audit_repo = AuditLogRepository(db)

        registration = registration_repo.get_by_id_with_details(registration_id)

        if not registration:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found.")

        if registration.attendee.user_id != current_user.id and current_user.role.value not in ("ADMIN", "EVENT_ORGANIZER"):

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only cancel your own registration.")

        if registration.registration_status == RegistrationStatus.CANCELLED:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This registration is already cancelled.")

        registration.registration_status = RegistrationStatus.CANCELLED

        audit_repo.log(
            user_id=current_user.id,
            action="CANCEL",
            entity_type="Registration",
            entity_id=registration.id,
            description="Registration cancelled"
        )

        db.commit()

        db.refresh(registration)

        logger.info(f"Registration cancelled successfully : {registration_id}")

        return {"message": "Registration cancelled successfully.", "data": registration}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Registration cancellation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to cancel registration.")