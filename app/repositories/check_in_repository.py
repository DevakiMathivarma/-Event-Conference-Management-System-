from sqlalchemy.orm import Session, joinedload

from app.models.check_in import CheckIn
from app.repositories.base_repository import BaseRepository


class CheckInRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(CheckIn, db)

    def get_by_registration_id(self, registration_id: int):

        return self.db.query(CheckIn).options(joinedload(CheckIn.checked_in_by)).filter(CheckIn.registration_id == registration_id).first()

    def list_for_event(self, event_id: int):

        from app.models.registration import Registration

        return (
            self.db.query(CheckIn)
            .join(Registration, CheckIn.registration_id == Registration.id)
            .options(joinedload(CheckIn.checked_in_by))
            .filter(Registration.event_id == event_id)
            .all()
        )