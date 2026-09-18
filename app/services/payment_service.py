# app/services/payment_service.py

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentStatus
from app.models.purchase import Purchase, PurchaseStatus
from app.models.registration import RegistrationStatus
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment_schema import PaymentCreate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_payment(purchase_id: int, data: PaymentCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Recording payment attempt : purchase {purchase_id}")

        purchase_repo = BaseRepository(Purchase, db)
        payment_repo = PaymentRepository(db)
        audit_repo = AuditLogRepository(db)

        purchase = purchase_repo.get_by_id(purchase_id)

        if not purchase:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found.")

        existing_payment = payment_repo.get_by_purchase_id(purchase_id)

        if existing_payment:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This purchase already has a payment recorded.")

        # prevent duplicate transactions - friendly pre-check, backed
        # by the database's own unique constraint
        existing_transaction = db.query(Payment).filter(Payment.transaction_id == data.transaction_id).first()

        if existing_transaction:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This transaction ID has already been used.")

        # payment amount must match purchase amount - level 8 business
        # rule. the amount always comes from the purchase itself, never
        # trusted from the client. starts PENDING, matching the model's
        # own default - not confirmed as SUCCESS until a real, separate
        # confirmation step, so "failed payments should not confirm
        # ticket purchase" is genuinely checkable, not just assumed
        payment = Payment(
            purchase_id=purchase_id,
            transaction_id=data.transaction_id,
            payment_method=data.payment_method,
            amount=purchase.total_amount,
            payment_status=PaymentStatus.PENDING
        )

        payment_repo.add(payment)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Payment",
            entity_id=payment.id,
            description=f"Payment attempt of {purchase.total_amount} recorded for purchase {purchase_id}"
        )

        db.commit()

        payment = payment_repo.get_by_id_with_details(payment.id)

        logger.info(f"Payment attempt recorded successfully : {payment.id}")

        return {"message": "Payment recorded. Awaiting confirmation.", "data": payment}

    except HTTPException:

        raise

    except IntegrityError:

        db.rollback()

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This transaction ID has already been used.")

    except Exception as error:

        db.rollback()

        logger.error(f"Payment recording failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to record payment.")


def confirm_payment(payment_id: int, is_success: bool, current_user, db: Session) -> dict:

    try:

        logger.info(f"Confirming payment : {payment_id}, is_success={is_success}")

        payment_repo = PaymentRepository(db)
        audit_repo = AuditLogRepository(db)

        payment = payment_repo.get_by_id_with_details(payment_id)

        if not payment:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")

        if payment.payment_status != PaymentStatus.PENDING:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This payment has already been resolved.")

        purchase = payment.purchase
        registration = purchase.registration

        if is_success:

            # successful payment should confirm ticket purchase and
            # registration - level 8 business rule, cascading all the
            # way up
            payment.payment_status = PaymentStatus.SUCCESS
            purchase.status = PurchaseStatus.CONFIRMED
            registration.registration_status = RegistrationStatus.CONFIRMED

        else:

            # failed payments should not confirm ticket purchase -
            # level 8 business rule. the reserved tickets get released
            # back, since this purchase never actually went through -
            # closing the earlier flagged gap
            payment.payment_status = PaymentStatus.FAILED
            purchase.status = PurchaseStatus.CANCELLED
            purchase.ticket.available_quantity += purchase.quantity

        audit_repo.log(
            user_id=current_user.id,
            action="CONFIRM" if is_success else "FAIL",
            entity_type="Payment",
            entity_id=payment.id,
            description=f"Payment {'confirmed' if is_success else 'marked as failed'}"
        )

        db.commit()

        db.refresh(payment)

        if is_success:

            # level 13-equivalent notifications, wired in immediately,
            # only on the genuine success path
            from app.utils.pdf import generate_ticket_pdf
            from app.tasks import send_payment_success_email, send_ticket_confirmation_email
            from app.utils.qr_code import generate_registration_qr_code

            attendee_user = current_user
            event = registration.event

            send_payment_success_email.delay(attendee_user.email, attendee_user.full_name, str(purchase.total_amount), event.event_name)

            ticket_path = generate_ticket_pdf(
                purchase_id=purchase.id,
                event_name=event.event_name,
                attendee_name=attendee_user.full_name,
                ticket_type=purchase.ticket.ticket_type,
                quantity=purchase.quantity,
                total_amount=str(purchase.total_amount),
                event_start_date=str(event.start_date)
            )

            send_ticket_confirmation_email.delay(attendee_user.email, attendee_user.full_name, event.event_name, ticket_path)

            generate_registration_qr_code(registration.id, f"REGISTRATION-{registration.id}")

        logger.info(f"Payment resolved successfully : {payment_id}, success={is_success}")

        return {"message": f"Payment {'confirmed' if is_success else 'marked as failed'}.", "data": payment}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Payment confirmation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to confirm payment.")


def get_payment_by_id(payment_id: int, db: Session) -> dict:

    payment_repo = PaymentRepository(db)

    payment = payment_repo.get_by_id_with_details(payment_id)

    if not payment:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")

    return {"message": "Payment fetched successfully.", "data": payment}


def get_all_payments(
    db: Session,
    page: int = 1,
    limit: int = 10,
    payment_status=None,
    payment_method=None,
    start_date=None,
    end_date=None,
    sort_by: str = "payment_date",
    sort_order: str = "desc"
) -> dict:

    logger.info("Fetching payments list.")

    payment_repo = PaymentRepository(db)

    sortable_columns = {"payment_date": Payment.payment_date, "amount": Payment.amount}

    sort_column = sortable_columns.get(sort_by, Payment.payment_date)

    payments, total_records = payment_repo.list_payments(payment_status, payment_method, start_date, end_date, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Payments fetched successfully.", "data": payments, "pagination": get_pagination(total_records, page, limit)}