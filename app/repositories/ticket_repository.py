from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.repositories.base_repository import BaseRepository


class TicketRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Ticket, db)

    def list_for_event(self, event_id: int):

        return self.db.query(Ticket).filter(Ticket.event_id == event_id).all()