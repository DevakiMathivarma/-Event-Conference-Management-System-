from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.attendee import Attendee
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class AttendeeRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Attendee, db)

    def get_by_id_with_details(self, attendee_id: int):

        return self.db.query(Attendee).options(joinedload(Attendee.user)).filter(Attendee.id == attendee_id).first()

    def list_attendees(self, search, sort_column, sort_order, offset, limit):

        query = self.db.query(Attendee).options(joinedload(Attendee.user)).join(User, Attendee.user_id == User.id)

        if search:

            search_term = f"%{search}%"

            query = query.filter(or_(User.full_name.ilike(search_term), User.email.ilike(search_term)))

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        attendees = query.offset(offset).limit(limit).all()

        return attendees, total_records