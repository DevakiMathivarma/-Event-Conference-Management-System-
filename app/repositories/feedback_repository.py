from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.repositories.base_repository import BaseRepository


class FeedbackRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Feedback, db)

    def get_existing_for_target(self, registration_id: int, event_id: int, speaker_id, session_id):

        query = self.db.query(Feedback).filter(Feedback.registration_id == registration_id, Feedback.event_id == event_id)

        # match the exact same target combination - null-safe
        # comparison, since speaker_id/session_id are both optional
        if speaker_id:

            query = query.filter(Feedback.speaker_id == speaker_id)

        else:

            query = query.filter(Feedback.speaker_id.is_(None))

        if session_id:

            query = query.filter(Feedback.session_id == session_id)

        else:

            query = query.filter(Feedback.session_id.is_(None))

        return query.first()

    def list_feedback(self, event_id, speaker_id, session_id, sort_column, sort_order, offset, limit):

        query = self.db.query(Feedback)

        if event_id:

            query = query.filter(Feedback.event_id == event_id)

        if speaker_id:

            query = query.filter(Feedback.speaker_id == speaker_id)

        if session_id:

            query = query.filter(Feedback.session_id == session_id)

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        feedback_entries = query.offset(offset).limit(limit).all()

        return feedback_entries, total_records