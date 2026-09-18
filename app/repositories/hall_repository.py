from sqlalchemy.orm import Session

from app.models.hall import Hall
from app.repositories.base_repository import BaseRepository


class HallRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Hall, db)

    def list_for_venue(self, venue_id: int):

        return self.db.query(Hall).filter(Hall.venue_id == venue_id).all()