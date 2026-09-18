from fastapi import HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.models.event import Event
from app.models.hall import Hall
from app.models.session import Session as SessionModel
from app.models.speaker import Speaker
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.session_schema import SessionCreate, SessionUpdate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def _check_session_business_rules(data_dict: dict, event, session_repo: SessionRepository, exclude_session_id=None):

    # session timing must fall within event timing - level 5 business rule
    if not (event.start_date <= data_dict["start_time"] and data_dict["end_time"] <= event.end_date):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session timing must fall within the event's own timing ({event.start_date} to {event.end_date})."
        )

    # hall cannot have overlapping sessions - level 5 business rule,
    # using the shared overlap helper
    hall_conflicts = session_repo.get_overlapping_sessions(
        "hall_id", data_dict["hall_id"], data_dict["start_time"], data_dict["end_time"], exclude_session_id
    )

    if hall_conflicts:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This hall already has an overlapping session.")

    # speaker cannot have overlapping sessions - level 5 business rule,
    # same shared helper, different column, only checked if a speaker
    # is actually assigned
    if data_dict.get("speaker_id"):

        speaker_conflicts = session_repo.get_overlapping_sessions(
            "speaker_id", data_dict["speaker_id"], data_dict["start_time"], data_dict["end_time"], exclude_session_id
        )

        if speaker_conflicts:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This speaker already has an overlapping session.")


def create_session(data: SessionCreate, current_user, db: DBSession) -> dict:

    try:

        logger.info(f"Creating session : event {data.event_id}, {data.title}")

        event_repo = BaseRepository(Event, db)
        hall_repo = BaseRepository(Hall, db)
        speaker_repo = BaseRepository(Speaker, db)
        session_repo = SessionRepository(db)
        audit_repo = AuditLogRepository(db)

        event = event_repo.get_by_id(data.event_id)

        if not event:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

        hall = hall_repo.get_by_id(data.hall_id)

        if not hall:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hall not found.")

        if data.speaker_id:

            speaker = speaker_repo.get_by_id(data.speaker_id)

            if not speaker:

                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaker not found.")

            # inactive speakers cannot be assigned - level 4 business rule
            if not speaker.is_active:

                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This speaker is not currently available for assignment.")

        _check_session_business_rules(data.model_dump(), event, session_repo)

        session = SessionModel(**data.model_dump())

        session_repo.add(session)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Session",
            entity_id=session.id,
            description=f"Session '{data.title}' created for event {data.event_id}"
        )

        db.commit()

        session = session_repo.get_by_id_with_details(session.id)

        logger.info(f"Session created successfully : {session.id}")

        return {"message": "Session created successfully.", "data": session}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Session creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create session.")


def get_sessions_for_event(
    db: DBSession,
    page: int = 1,
    limit: int = 10,
    event_id=None,
    speaker_id=None,
    session_type: str | None = None,
    date_filter=None,
    sort_by: str = "start_time",
    sort_order: str = "asc"
) -> dict:

    logger.info("Fetching sessions list.")

    session_repo = SessionRepository(db)

    sortable_columns = {"start_time": SessionModel.start_time, "created_at": SessionModel.created_at}

    sort_column = sortable_columns.get(sort_by, SessionModel.start_time)

    sessions, total_records = session_repo.list_sessions(event_id, speaker_id, session_type, date_filter, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Sessions fetched successfully.", "data": sessions, "pagination": get_pagination(total_records, page, limit)}


def get_session_by_id(session_id: int, db: DBSession) -> dict:

    session_repo = SessionRepository(db)

    session = session_repo.get_by_id_with_details(session_id)

    if not session:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    return {"message": "Session fetched successfully.", "data": session}


def update_session(session_id: int, data: SessionUpdate, current_user, db: DBSession) -> dict:

    try:

        logger.info(f"Updating session : {session_id}")

        session_repo = SessionRepository(db)
        event_repo = BaseRepository(Event, db)
        speaker_repo = BaseRepository(Speaker, db)
        audit_repo = AuditLogRepository(db)

        session = session_repo.get_by_id_with_details(session_id)

        if not session:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

        event = event_repo.get_by_id(session.event_id)

        update_data = data.model_dump(exclude_unset=True)

        merged = {
            "start_time": update_data.get("start_time", session.start_time),
            "end_time": update_data.get("end_time", session.end_time),
            "hall_id": update_data.get("hall_id", session.hall_id),
            "speaker_id": update_data.get("speaker_id", session.speaker_id),
        }

        if merged.get("speaker_id"):

            speaker = speaker_repo.get_by_id(merged["speaker_id"])

            if speaker and not speaker.is_active:

                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This speaker is not currently available for assignment.")

        _check_session_business_rules(merged, event, session_repo, exclude_session_id=session_id)

        for key, value in update_data.items():

            setattr(session, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Session",
            entity_id=session.id,
            description="Session updated"
        )

        db.commit()

        db.refresh(session)

        logger.info(f"Session updated successfully : {session_id}")

        return {"message": "Session updated successfully.", "data": session}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Session update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update session.")


def delete_session(session_id: int, current_user, db: DBSession) -> dict:

    try:

        logger.info(f"Deleting session : {session_id}")

        session_repo = SessionRepository(db)
        audit_repo = AuditLogRepository(db)

        session = session_repo.get_by_id(session_id)

        if not session:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

        session_repo.delete(session)

        audit_repo.log(
            user_id=current_user.id,
            action="DELETE",
            entity_type="Session",
            entity_id=session_id,
            description="Session removed"
        )

        db.commit()

        logger.info(f"Session deleted successfully : {session_id}")

        return {"message": "Session deleted successfully."}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Session deletion failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to delete session.")