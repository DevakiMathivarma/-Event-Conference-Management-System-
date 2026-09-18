from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.registration import Registration, RegistrationStatus
from app.models.session import Session as SessionModel
from app.models.session_booking import SessionBooking
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.session_booking_repository import SessionBookingRepository
from app.utils.logger import logger


def create_session_booking(session_id: int, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating session booking : attendee {current_user.attendee.id}, session {session_id}")

        session_repo = BaseRepository(SessionModel, db)
        booking_repo = SessionBookingRepository(db)
        audit_repo = AuditLogRepository(db)

        target_session = session_repo.get_by_id(session_id)

        if not target_session:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

        # find this attendee's registration for the session's own
        # parent event
        registration = db.query(Registration).filter(
            Registration.attendee_id == current_user.attendee.id, Registration.event_id == target_session.event_id
        ).first()

        if not registration:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You must be registered for this event before booking a session.")

        # only confirmed attendees can book sessions - level 9 business rule
        if registration.registration_status != RegistrationStatus.CONFIRMED:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your registration must be confirmed before booking sessions.")

        # prevent duplicate session bookings - friendly pre-check,
        # backed by the database's own unique constraint
        existing = booking_repo.get_by_registration_and_session(registration.id, session_id)

        if existing:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already booked this session.")

        # session capacity cannot be exceeded - level 9 business rule
        current_bookings = booking_repo.count_for_session(session_id)

        if current_bookings >= target_session.capacity:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This session has reached its capacity.")

        booking = SessionBooking(registration_id=registration.id, session_id=session_id)

        booking_repo.add(booking)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="SessionBooking",
            entity_id=booking.id,
            description=f"Session {session_id} booked"
        )

        db.commit()

        db.refresh(booking)

        logger.info(f"Session booking created successfully : {booking.id}")

        return {"message": "Session booked successfully.", "data": booking}

    except HTTPException:

        raise

    except IntegrityError:

        db.rollback()

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already booked this session.")

    except Exception as error:

        db.rollback()

        logger.error(f"Session booking creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to book session.")


def get_sessions_for_attendee(attendee_id: int, db: Session) -> dict:

    booking_repo = SessionBookingRepository(db)

    bookings = booking_repo.list_for_attendee(attendee_id)

    return {"message": "Booked sessions fetched successfully.", "data": bookings}


def delete_session_booking(booking_id: int, current_user, db: Session) -> dict:

    try:

        logger.info(f"Deleting session booking : {booking_id}")

        booking_repo = SessionBookingRepository(db)
        audit_repo = AuditLogRepository(db)

        booking = booking_repo.get_by_id(booking_id)

        if not booking or booking.registration.attendee.user_id != current_user.id:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session booking not found.")

        booking_repo.delete(booking)

        audit_repo.log(
            user_id=current_user.id,
            action="DELETE",
            entity_type="SessionBooking",
            entity_id=booking_id,
            description="Session booking cancelled"
        )

        db.commit()

        logger.info(f"Session booking deleted successfully : {booking_id}")

        return {"message": "Session booking cancelled successfully."}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Session booking deletion failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to cancel session booking.")