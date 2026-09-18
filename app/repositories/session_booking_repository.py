# app/repositories/session_booking_repository.py

from sqlalchemy.orm import Session, joinedload

from app.models.session_booking import SessionBooking
from app.repositories.base_repository import BaseRepository


class SessionBookingRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(SessionBooking, db)

    def get_by_registration_and_session(self, registration_id: int, session_id: int):

        return self.db.query(SessionBooking).filter(
            SessionBooking.registration_id == registration_id, SessionBooking.session_id == session_id
        ).first()

    def count_for_session(self, session_id: int) -> int:

        return self.db.query(SessionBooking).filter(SessionBooking.session_id == session_id).count()

    def list_for_attendee(self, attendee_id: int):

        from app.models.registration import Registration

        return (
            self.db.query(SessionBooking)
            .join(Registration, SessionBooking.registration_id == Registration.id)
            .options(joinedload(SessionBooking.session))
            .filter(Registration.attendee_id == attendee_id)
            .all()
        )