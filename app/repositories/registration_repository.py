from sqlalchemy.orm import Session, joinedload

from app.models.attendee import Attendee
from app.models.registration import Registration
from app.repositories.base_repository import BaseRepository


class RegistrationRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Registration, db)

    def get_by_id_with_details(self, registration_id: int):

        return (
            self.db.query(Registration)
            .options(joinedload(Registration.attendee).joinedload(Attendee.user), joinedload(Registration.event))
            .filter(Registration.id == registration_id)
            .first()
        )

    def get_by_attendee_and_event(self, attendee_id: int, event_id: int):

        return self.db.query(Registration).filter(Registration.attendee_id == attendee_id, Registration.event_id == event_id).first()

    def count_confirmed_for_event(self, event_id: int) -> int:

        from app.models.registration import RegistrationStatus

        return self.db.query(Registration).filter(Registration.event_id == event_id, Registration.registration_status == RegistrationStatus.CONFIRMED).count()

    def list_registrations(self, event_id, status, start_date, end_date, sort_column, sort_order, offset, limit):

        query = self.db.query(Registration).options(joinedload(Registration.attendee).joinedload(Attendee.user), joinedload(Registration.event))

        if event_id:

            query = query.filter(Registration.event_id == event_id)

        if status:

            query = query.filter(Registration.registration_status == status)

        if start_date:

            query = query.filter(Registration.registration_date >= start_date)

        if end_date:

            query = query.filter(Registration.registration_date <= end_date)

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        registrations = query.offset(offset).limit(limit).all()

        return registrations, total_records