from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.check_in_repository import CheckInRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.feedback_schema import FeedbackCreate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_feedback(data: FeedbackCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating feedback : attendee {current_user.attendee.id}, event {data.event_id}")

        from app.models.registration import Registration

        feedback_repo = FeedbackRepository(db)
        checkin_repo = CheckInRepository(db)
        audit_repo = AuditLogRepository(db)

        registration = db.query(Registration).filter(
            Registration.attendee_id == current_user.attendee.id, Registration.event_id == data.event_id
        ).first()

        if not registration:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are not registered for this event.")

        # only attendees who checked in can provide feedback - level 12
        # business rule
        check_in = checkin_repo.get_by_registration_id(registration.id)

        if not check_in or check_in.check_in_time is None:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You must have checked in to this event to provide feedback.")

        # prevent duplicate feedback for the same target - our own
        # consistent application of the task's session-specific
        # wording across event/speaker/session, matching the reasoning
        # locked in at the schema stage
        existing = feedback_repo.get_existing_for_target(registration.id, data.event_id, data.speaker_id, data.session_id)

        if existing:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already submitted feedback for this.")

        feedback = Feedback(registration_id=registration.id, **data.model_dump())

        feedback_repo.add(feedback)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Feedback",
            entity_id=feedback.id,
            description=f"Feedback submitted for event {data.event_id}"
        )

        db.commit()

        db.refresh(feedback)

        logger.info(f"Feedback created successfully : {feedback.id}")

        return {"message": "Feedback submitted successfully.", "data": feedback}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Feedback creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to submit feedback.")


def get_all_feedback(
    db: Session,
    page: int = 1,
    limit: int = 10,
    event_id=None,
    speaker_id=None,
    session_id=None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> dict:

    logger.info("Fetching feedback list.")

    feedback_repo = FeedbackRepository(db)

    sortable_columns = {"created_at": Feedback.created_at, "rating": Feedback.rating}

    sort_column = sortable_columns.get(sort_by, Feedback.created_at)

    feedback_entries, total_records = feedback_repo.list_feedback(event_id, speaker_id, session_id, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Feedback fetched successfully.", "data": feedback_entries, "pagination": get_pagination(total_records, page, limit)}