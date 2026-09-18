# app/repositories/event_repository.py

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.event import Event
from app.repositories.base_repository import BaseRepository


class EventRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Event, db)

    def get_by_id_with_details(self, event_id: int):

        return self.db.query(Event).options(joinedload(Event.organizer)).filter(Event.id == event_id).first()

    def list_events(self, event_type, city, status, available_only, start_date, end_date, search, sort_column, sort_order, offset, limit):

        from app.models.session import Session as SessionModel
        from app.models.hall import Hall
        from app.models.venue import Venue

        query = self.db.query(Event).options(joinedload(Event.organizer))

        if event_type:

            query = query.filter(Event.event_type == event_type)

        if status:

            query = query.filter(Event.status == status)

        # real city filtering, now that session -> hall -> venue
        # actually connects an event to a real city - matching events
        # that have at least one session scheduled in a hall within
        # this city. events with no sessions scheduled yet won't match
        # any city filter, since there's genuinely no city data
        # connected to them yet - a correct outcome given the actual
        # data model, not a bug
        if city:

            query = (
                query.join(SessionModel, SessionModel.event_id == Event.id)
                .join(Hall, SessionModel.hall_id == Hall.id)
                .join(Venue, Hall.venue_id == Venue.id)
                .filter(Venue.city.ilike(f"%{city}%"))
                .distinct()
            )

        if start_date:

            query = query.filter(Event.start_date >= start_date)

        if end_date:

            query = query.filter(Event.end_date <= end_date)

        if search:

            search_term = f"%{search}%"

            query = query.filter(or_(Event.event_name.ilike(search_term), Event.description.ilike(search_term)))

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        all_events = query.all()

        # available_only filters on remaining capacity, which needs a
        # live count of confirmed registrations per event - a genuine
        # calculated value, same reasoning as the food delivery
        # platform's restaurant-rating filter, done in python after
        # the main query rather than as a sql filter
        if available_only:

            from app.models.registration import Registration, RegistrationStatus

            filtered = []

            for event in all_events:

                confirmed_count = self.db.query(Registration).filter(
                    Registration.event_id == event.id, Registration.registration_status == RegistrationStatus.CONFIRMED
                ).count()

                if confirmed_count < event.capacity:

                    filtered.append(event)

            all_events = filtered

        total_records = len(all_events)

        events = all_events[offset:offset + limit]

        return events, total_records

    def get_events_starting_within(self, days: int):

        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days)

        return self.db.query(Event).filter(Event.start_date <= cutoff, Event.start_date >= now).all()