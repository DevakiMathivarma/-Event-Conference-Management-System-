from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.venue import Venue
from app.repositories.base_repository import BaseRepository


class VenueRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Venue, db)

    def get_by_id_with_details(self, venue_id: int):

        return self.db.query(Venue).options(joinedload(Venue.created_by)).filter(Venue.id == venue_id).first()

    def list_venues(self, city, status, search, sort_column, sort_order, offset, limit):

        query = self.db.query(Venue).options(joinedload(Venue.created_by))

        if city:

            query = query.filter(Venue.city.ilike(f"%{city}%"))

        if status:

            query = query.filter(Venue.status == status)

        if search:

            search_term = f"%{search}%"

            query = query.filter(or_(Venue.venue_name.ilike(search_term), Venue.address.ilike(search_term)))

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        venues = query.offset(offset).limit(limit).all()

        return venues, total_records