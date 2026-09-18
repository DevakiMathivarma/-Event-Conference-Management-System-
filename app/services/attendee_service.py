from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.attendee import Attendee
from app.models.user import User, UserRole
from app.repositories.attendee_repository import AttendeeRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.attendee_schema import AttendeeCreate, AttendeeUpdate
from app.utils.hashing import hash_password
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_attendee(data: AttendeeCreate, db: Session) -> dict:

    try:

        logger.info(f"Creating attendee : {data.email}")

        user_repo = UserRepository(db)
        attendee_repo = AttendeeRepository(db)
        audit_repo = AuditLogRepository(db)

        existing_user = user_repo.get_by_email_or_phone(data.email, data.phone)

        if existing_user:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or phone number already registered.")

        user = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=UserRole.ATTENDEE
        )

        user_repo.add(user)

        db.flush()

        attendee = Attendee(user_id=user.id, organization=data.organization, designation=data.designation)

        attendee_repo.add(attendee)

        db.flush()

        audit_repo.log(
            user_id=user.id,
            action="CREATE",
            entity_type="Attendee",
            entity_id=attendee.id,
            description="Attendee self-registered"
        )

        db.commit()

        attendee = attendee_repo.get_by_id_with_details(attendee.id)

        logger.info(f"Attendee created successfully : {attendee.id}")

        return {"message": "Attendee registered successfully.", "data": attendee}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Attendee creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create attendee.")


def get_attendee_by_id(attendee_id: int, db: Session) -> dict:

    attendee_repo = AttendeeRepository(db)

    attendee = attendee_repo.get_by_id_with_details(attendee_id)

    if not attendee:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendee not found.")

    return {"message": "Attendee fetched successfully.", "data": attendee}


def get_all_attendees(db: Session, page: int = 1, limit: int = 10, search: str | None = None, sort_by: str = "created_at", sort_order: str = "desc") -> dict:

    logger.info("Fetching attendees list.")

    attendee_repo = AttendeeRepository(db)

    sortable_columns = {"created_at": Attendee.created_at}

    sort_column = sortable_columns.get(sort_by, Attendee.created_at)

    attendees, total_records = attendee_repo.list_attendees(search, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Attendees fetched successfully.", "data": attendees, "pagination": get_pagination(total_records, page, limit)}


def update_attendee(attendee_id: int, data: AttendeeUpdate, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Updating attendee : {attendee_id}")

        attendee_repo = AttendeeRepository(db)
        audit_repo = AuditLogRepository(db)

        attendee = attendee_repo.get_by_id_with_details(attendee_id)

        if not attendee:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendee not found.")

        if attendee.user_id != current_user.id:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendee not found.")

        update_data = data.model_dump(exclude_unset=True)

        user_fields = {"full_name", "phone"}

        for key, value in update_data.items():

            if key in user_fields:

                setattr(attendee.user, key, value)

            else:

                setattr(attendee, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Attendee",
            entity_id=attendee.id,
            description="Attendee profile updated"
        )

        db.commit()

        db.refresh(attendee)

        logger.info(f"Attendee updated successfully : {attendee_id}")

        return {"message": "Attendee updated successfully.", "data": attendee}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Attendee update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update attendee.")