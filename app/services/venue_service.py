from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.venue import Venue
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.venue_repository import VenueRepository
from app.schemas.venue_schema import VenueCreate, VenueUpdate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_venue(data: VenueCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating venue : {data.venue_name}")

        venue_repo = VenueRepository(db)
        audit_repo = AuditLogRepository(db)

        venue = Venue(**data.model_dump(), created_by_user_id=current_user.id)

        venue_repo.add(venue)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Venue",
            entity_id=venue.id,
            description=f"Venue '{data.venue_name}' created"
        )

        db.commit()

        venue = venue_repo.get_by_id_with_details(venue.id)

        logger.info(f"Venue created successfully : {venue.id}")

        return {"message": "Venue created successfully.", "data": venue}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Venue creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create venue.")


def get_all_venues(
    db: Session,
    page: int = 1,
    limit: int = 10,
    city: str | None = None,
    status_filter=None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> dict:

    logger.info("Fetching venues list.")

    venue_repo = VenueRepository(db)

    sortable_columns = {"created_at": Venue.created_at, "venue_name": Venue.venue_name}

    sort_column = sortable_columns.get(sort_by, Venue.created_at)

    venues, total_records = venue_repo.list_venues(city, status_filter, search, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Venues fetched successfully.", "data": venues, "pagination": get_pagination(total_records, page, limit)}