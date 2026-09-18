from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.event import Event
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.event_repository import EventRepository
from app.schemas.event_schema import EventCreate, EventUpdate, EventResponse
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset
from app.utils.redis_cache import get_cache, set_cache, delete_cache

CACHE_TTL = 600


def create_event(data: EventCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating event : {data.event_name}")

        event_repo = EventRepository(db)
        audit_repo = AuditLogRepository(db)

        event = Event(**data.model_dump(), organizer_id=current_user.id)

        event_repo.add(event)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Event",
            entity_id=event.id,
            description=f"Event '{data.event_name}' created"
        )

        db.commit()

        event = event_repo.get_by_id_with_details(event.id)

        logger.info(f"Event created successfully : {event.id}")

        return {"message": "Event created successfully.", "data": event}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Event creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create event.")


# get by id - cached (bonus feature, redis)
def get_event_by_id(event_id: int, db: Session) -> dict:

    logger.info(f"Fetching event by id : {event_id}")

    cache_key = f"event:{event_id}"

    cached_event = get_cache(cache_key)

    if cached_event:

        logger.info(f"Event cache hit : {event_id}")

        return {"message": "Event fetched successfully.", "data": cached_event}

    event_repo = EventRepository(db)

    event = event_repo.get_by_id_with_details(event_id)

    if not event:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    set_cache(cache_key, EventResponse.model_validate(event).model_dump(mode="json"), expire=CACHE_TTL)

    return {"message": "Event fetched successfully.", "data": event}


def get_all_events(
    db: Session,
    page: int = 1,
    limit: int = 10,
    event_type=None,
    city: str | None = None,
    status_filter=None,
    available_only: bool = False,
    start_date=None,
    end_date=None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> dict:

    logger.info("Fetching events list.")

    event_repo = EventRepository(db)

    sortable_columns = {"created_at": Event.created_at, "start_date": Event.start_date}

    sort_column = sortable_columns.get(sort_by, Event.created_at)

    events, total_records = event_repo.list_events(
        event_type, city, status_filter, available_only, start_date, end_date, search, sort_column, sort_order, get_offset(page, limit), limit
    )

    return {"message": "Events fetched successfully.", "data": events, "pagination": get_pagination(total_records, page, limit)}


def update_event(event_id: int, data: EventUpdate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Updating event : {event_id}")

        event_repo = EventRepository(db)
        audit_repo = AuditLogRepository(db)

        event = event_repo.get_by_id_with_details(event_id)

        if not event:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

        if current_user.role.value == "EVENT_ORGANIZER" and event.organizer_id != current_user.id:

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own event.")

        update_data = data.model_dump(exclude_unset=True)

        new_end = update_data.get("end_date", event.end_date)
        new_registration_end = update_data.get("registration_end", event.registration_end)

        if new_end <= event.start_date:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_date must be after start_date.")

        if new_registration_end > event.start_date:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="registration_end cannot be after start_date.")

        for key, value in update_data.items():

            setattr(event, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Event",
            entity_id=event.id,
            description="Event updated"
        )

        db.commit()

        db.refresh(event)

        # invalidate the cache now that the event's own data has changed
        delete_cache(f"event:{event_id}")

        logger.info(f"Event updated successfully : {event_id}")

        return {"message": "Event updated successfully.", "data": event}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Event update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update event.")


def delete_event(event_id: int, current_user, db: Session) -> dict:

    try:

        logger.info(f"Deleting event : {event_id}")

        event_repo = EventRepository(db)
        audit_repo = AuditLogRepository(db)

        event = event_repo.get_by_id_with_details(event_id)

        if not event:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

        if current_user.role.value == "EVENT_ORGANIZER" and event.organizer_id != current_user.id:

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own event.")

        from app.models.event import EventStatus

        event.status = EventStatus.CANCELLED

        audit_repo.log(
            user_id=current_user.id,
            action="DELETE",
            entity_type="Event",
            entity_id=event.id,
            description="Event cancelled (soft delete)"
        )

        db.commit()

        # invalidate the cache now that the event's status has changed
        delete_cache(f"event:{event_id}")

        # notify every genuinely registered attendee - the event
        # cancellation notification gap, now closed. only confirmed
        # and pending registrations matter here; already-cancelled ones
        # don't need a second cancellation notice
        from app.models.registration import Registration, RegistrationStatus
        from app.tasks import send_event_cancellation_email

        affected_registrations = db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.registration_status.in_([RegistrationStatus.CONFIRMED, RegistrationStatus.PENDING])
        ).all()

        for registration in affected_registrations:

            attendee_user = registration.attendee.user

            send_event_cancellation_email.delay(attendee_user.email, attendee_user.full_name, event.event_name)

        logger.info(f"Event cancelled successfully : {event_id}, {len(affected_registrations)} attendees notified")

        return {"message": "Event cancelled successfully."}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Event deletion failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to delete event.")