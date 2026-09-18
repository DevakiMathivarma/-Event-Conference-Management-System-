from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.speaker import Speaker
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class SpeakerRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Speaker, db)

    def get_by_id_with_details(self, speaker_id: int):

        return self.db.query(Speaker).options(joinedload(Speaker.user), joinedload(Speaker.created_by)).filter(Speaker.id == speaker_id).first()

    def list_speakers(self, expertise, active_only, search, sort_column, sort_order, offset, limit):

        query = self.db.query(Speaker).options(joinedload(Speaker.user)).join(User, Speaker.user_id == User.id)

        if expertise:

            query = query.filter(Speaker.expertise.ilike(f"%{expertise}%"))

        if active_only:

            query = query.filter(Speaker.is_active == True)

        if search:

            search_term = f"%{search}%"

            query = query.filter(or_(User.full_name.ilike(search_term), Speaker.company.ilike(search_term)))

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        speakers = query.offset(offset).limit(limit).all()

        return speakers, total_records