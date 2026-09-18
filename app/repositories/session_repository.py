from sqlalchemy.orm import Session, joinedload

from app.models.session import Session as SessionModel
from app.repositories.base_repository import BaseRepository


class SessionRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(SessionModel, db)

    def get_by_id_with_details(self, session_id: int):

        return (
            self.db.query(SessionModel)
            .options(joinedload(SessionModel.speaker), joinedload(SessionModel.hall))
            .filter(SessionModel.id == session_id)
            .first()
        )

    def list_for_event(self, event_id: int):

        return (
            self.db.query(SessionModel)
            .options(joinedload(SessionModel.speaker), joinedload(SessionModel.hall))
            .filter(SessionModel.event_id == event_id)
            .order_by(SessionModel.start_time.asc())
            .all()
        )

    def list_sessions(self, event_id, speaker_id, session_type, date_filter, sort_column, sort_order, offset, limit):

        query = self.db.query(SessionModel).options(joinedload(SessionModel.speaker), joinedload(SessionModel.hall))

        if event_id:

            query = query.filter(SessionModel.event_id == event_id)

        if speaker_id:

            query = query.filter(SessionModel.speaker_id == speaker_id)

        if session_type:

            query = query.filter(SessionModel.session_type.ilike(f"%{session_type}%"))

        if date_filter:

            from datetime import datetime, timedelta

            day_start = datetime.combine(date_filter, datetime.min.time())
            day_end = day_start + timedelta(days=1)

            query = query.filter(SessionModel.start_time >= day_start, SessionModel.start_time < day_end)

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        sessions = query.offset(offset).limit(limit).all()

        return sessions, total_records

    # generic overlap check - works for both hall_id and speaker_id,
    # since the underlying logic is identical, just checking a
    # different column each time - exactly the shared helper we
    # designed at the model stage
    def get_overlapping_sessions(self, column_name: str, column_value: int, start_time, end_time, exclude_session_id: int | None = None):

        column = getattr(SessionModel, column_name)

        query = self.db.query(SessionModel).filter(
            column == column_value,
            SessionModel.start_time < end_time,
            SessionModel.end_time > start_time
        )

        if exclude_session_id:

            query = query.filter(SessionModel.id != exclude_session_id)

        return query.all()

    def get_sessions_starting_within(self, hours: int):

        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours)

        return self.db.query(SessionModel).filter(SessionModel.start_time <= cutoff, SessionModel.start_time >= now).all()