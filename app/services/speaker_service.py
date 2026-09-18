from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.speaker import Speaker
from app.models.user import User, UserRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.speaker_repository import SpeakerRepository
from app.repositories.user_repository import UserRepository
from app.schemas.speaker_schema import SpeakerCreate, SpeakerUpdate
from app.utils.hashing import hash_password
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_speaker(data: SpeakerCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating speaker : {data.email}")

        user_repo = UserRepository(db)
        speaker_repo = SpeakerRepository(db)
        audit_repo = AuditLogRepository(db)

        existing_user = user_repo.get_by_email_or_phone(data.email, data.phone)

        if existing_user:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or phone number already registered.")

        user = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=UserRole.SPEAKER
        )

        user_repo.add(user)

        db.flush()

        speaker = Speaker(
            user_id=user.id,
            bio=data.bio,
            expertise=data.expertise,
            company=data.company,
            experience=data.experience,
            created_by_user_id=current_user.id
        )

        speaker_repo.add(speaker)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Speaker",
            entity_id=speaker.id,
            description=f"Speaker '{data.full_name}' registered"
        )

        db.commit()

        speaker = speaker_repo.get_by_id_with_details(speaker.id)

        logger.info(f"Speaker created successfully : {speaker.id}")

        return {"message": "Speaker registered successfully.", "data": speaker}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Speaker creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to register speaker.")


def get_speaker_by_id(speaker_id: int, db: Session) -> dict:

    speaker_repo = SpeakerRepository(db)

    speaker = speaker_repo.get_by_id_with_details(speaker_id)

    if not speaker:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaker not found.")

    return {"message": "Speaker fetched successfully.", "data": speaker}


def get_all_speakers(
    db: Session,
    page: int = 1,
    limit: int = 10,
    expertise: str | None = None,
    active_only: bool = False,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> dict:

    logger.info("Fetching speakers list.")

    speaker_repo = SpeakerRepository(db)

    sortable_columns = {"created_at": Speaker.created_at}

    sort_column = sortable_columns.get(sort_by, Speaker.created_at)

    speakers, total_records = speaker_repo.list_speakers(expertise, active_only, search, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Speakers fetched successfully.", "data": speakers, "pagination": get_pagination(total_records, page, limit)}


def update_speaker(speaker_id: int, data: SpeakerUpdate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Updating speaker : {speaker_id}")

        speaker_repo = SpeakerRepository(db)
        audit_repo = AuditLogRepository(db)

        speaker = speaker_repo.get_by_id_with_details(speaker_id)

        if not speaker:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaker not found.")

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():

            setattr(speaker, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Speaker",
            entity_id=speaker.id,
            description="Speaker updated"
        )

        db.commit()

        db.refresh(speaker)

        logger.info(f"Speaker updated successfully : {speaker_id}")

        return {"message": "Speaker updated successfully.", "data": speaker}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Speaker update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update speaker.")