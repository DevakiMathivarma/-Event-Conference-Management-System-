from sqlalchemy.orm import Session, joinedload

from app.models.certificate import Certificate
from app.repositories.base_repository import BaseRepository


class CertificateRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Certificate, db)

    def get_by_id_with_details(self, certificate_id: int):

        return (
            self.db.query(Certificate)
            .options(joinedload(Certificate.attendee), joinedload(Certificate.event))
            .filter(Certificate.id == certificate_id)
            .first()
        )

    def get_by_registration_id(self, registration_id: int):

        return self.db.query(Certificate).filter(Certificate.registration_id == registration_id).first()

    def list_for_attendee(self, attendee_id: int):

        return (
            self.db.query(Certificate)
            .options(joinedload(Certificate.event))
            .filter(Certificate.attendee_id == attendee_id)
            .all()
        )