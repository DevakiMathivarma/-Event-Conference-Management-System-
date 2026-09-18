from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.hall import Hall
from app.models.venue import Venue
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.hall_repository import HallRepository
from app.schemas.hall_schema import HallCreate
from app.utils.logger import logger


def create_hall(venue_id: int, data: HallCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating hall : venue {venue_id}, {data.hall_name}")

        venue_repo = BaseRepository(Venue, db)
        hall_repo = HallRepository(db)
        audit_repo = AuditLogRepository(db)

        venue = venue_repo.get_by_id(venue_id)

        if not venue:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found.")

        # hall capacity cannot exceed venue capacity - level 3 business
        # rule, a genuine cross-table check that can't live as a
        # database constraint, checked here at creation time
        if data.capacity > venue.capacity:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hall capacity cannot exceed the venue's own capacity of {venue.capacity}."
            )

        hall = Hall(venue_id=venue_id, **data.model_dump())

        hall_repo.add(hall)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Hall",
            entity_id=hall.id,
            description=f"Hall '{data.hall_name}' created in venue {venue_id}"
        )

        db.commit()

        db.refresh(hall)

        logger.info(f"Hall created successfully : {hall.id}")

        return {"message": "Hall created successfully.", "data": hall}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Hall creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create hall.")


def get_halls_for_venue(venue_id: int, db: Session) -> dict:

    hall_repo = HallRepository(db)

    halls = hall_repo.list_for_venue(venue_id)

    return {"message": "Halls fetched successfully.", "data": halls}