from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.event import EventStatus
from app.models.payment import Payment
from app.models.purchase import Purchase, PurchaseStatus
from app.models.refund import Refund, RefundStatus
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.refund_repository import RefundRepository
from app.schemas.refund_schema import RefundCreate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


# the exact tiered policy the task leaves unspecified - our own
# reasonable defaults, flagged clearly here rather than buried, and
# genuinely configurable through settings without touching this code
def _calculate_refund_percentage(event_start_date, cancellation_date, event_status: EventStatus) -> Decimal:

    # event cancelled by organizer -> full refund, always, regardless
    # of timing - the one case the task states with zero ambiguity
    if event_status == EventStatus.CANCELLED:

        return Decimal("1.00")

    if event_start_date.tzinfo is None:

        event_start_date = event_start_date.replace(tzinfo=timezone.utc)

    if cancellation_date.tzinfo is None:

        cancellation_date = cancellation_date.replace(tzinfo=timezone.utc)

    days_before_event = (event_start_date - cancellation_date).days

    if days_before_event >= settings.REFUND_FULL_REFUND_DAYS_BEFORE:

        return Decimal("1.00")

    elif days_before_event >= 0:

        return Decimal(str(settings.REFUND_PARTIAL_REFUND_PERCENTAGE))

    else:

        return Decimal("0.00")

def create_refund(purchase_id: int, data: RefundCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating refund : purchase {purchase_id}")

        purchase_repo = BaseRepository(Purchase, db)
        refund_repo = RefundRepository(db)
        audit_repo = AuditLogRepository(db)

        purchase = purchase_repo.get_by_id(purchase_id)

        if not purchase:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found.")

        existing_refund = refund_repo.get_by_purchase_id(purchase_id)

        if existing_refund:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This purchase has already been refunded.")

        payment = db.query(Payment).filter(Payment.purchase_id == purchase_id).first()

        if not payment:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This purchase has no recorded payment to refund.")

        registration = purchase.registration
        event = registration.event

        now = datetime.now(timezone.utc)

        refund_percentage = _calculate_refund_percentage(event.start_date, now, event.status)

        refund_amount = (payment.amount * refund_percentage).quantize(Decimal("0.01"))

        refund = Refund(
            purchase_id=purchase_id,
            cancellation_reason=data.cancellation_reason,
            refund_amount=refund_amount,
            status=RefundStatus.COMPLETED,
            refund_date=now,
            processed_by_user_id=current_user.id
        )

        refund_repo.add(refund)

        db.flush()

        purchase.status = PurchaseStatus.CANCELLED

        # deliberately not touching registration.registration_status
        # here - a refund is about the purchase/payment, not
        # necessarily the registration itself. cancelling the
        # registration outright is a separate, distinct action
        # (POST /registrations/{id}/cancel), not an automatic side
        # effect of getting refunded

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Refund",
            entity_id=refund.id,
            description=f"Refund of {refund_amount} processed ({refund_percentage * 100}% of {payment.amount})"
        )

        db.commit()

        db.refresh(refund)

        refund = refund_repo.get_by_id_with_details(refund.id)

        from app.tasks import send_refund_email

        attendee_user = registration.attendee.user

        send_refund_email.delay(attendee_user.email, attendee_user.full_name, event.event_name, str(refund_amount))

        logger.info(f"Refund created successfully : {refund.id}, amount {refund_amount}")

        return {"message": "Refund processed successfully.", "data": refund}

    except HTTPException:

        raise

    except IntegrityError:

        db.rollback()

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This purchase has already been refunded.")

    except Exception as error:

        db.rollback()

        logger.error(f"Refund creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to process refund.")
    
def get_refund_by_id(refund_id: int, db: Session) -> dict:

    refund_repo = RefundRepository(db)

    refund = refund_repo.get_by_id_with_details(refund_id)

    if not refund:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund not found.")

    return {"message": "Refund fetched successfully.", "data": refund}


def get_all_refunds(db: Session, page: int = 1, limit: int = 10) -> dict:

    refund_repo = RefundRepository(db)

    refunds, total_records = refund_repo.list_refunds(get_offset(page, limit), limit)

    return {"message": "Refunds fetched successfully.", "data": refunds, "pagination": get_pagination(total_records, page, limit)}