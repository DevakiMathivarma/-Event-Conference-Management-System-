from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.registration import Registration
from app.models.ticket import Ticket
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.purchase_repository import PurchaseRepository
from app.schemas.purchase_schema import PurchaseCreate
from app.utils.logger import logger

TAX_RATE = Decimal("0.05")


def create_purchase(ticket_id: int, data: PurchaseCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating purchase : ticket {ticket_id}, registration {data.registration_id}")

        ticket_repo = BaseRepository(Ticket, db)
        registration_repo = BaseRepository(Registration, db)
        purchase_repo = PurchaseRepository(db)
        audit_repo = AuditLogRepository(db)

        ticket = ticket_repo.get_by_id(ticket_id)

        if not ticket:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket category not found.")

        registration = registration_repo.get_by_id(data.registration_id)

        if not registration or registration.attendee.user_id != current_user.id:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found.")

        # expired ticket categories cannot be purchased - level 7
        # business rule, checked here at the actual moment of purchase
        now = datetime.now(timezone.utc)

        sale_start = ticket.sale_start if ticket.sale_start.tzinfo else ticket.sale_start.replace(tzinfo=timezone.utc)
        sale_end = ticket.sale_end if ticket.sale_end.tzinfo else ticket.sale_end.replace(tzinfo=timezone.utc)

        if now < sale_start or now > sale_end:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This ticket category is not currently available for purchase.")

        # sold tickets cannot exceed available quantity - level 7
        # business rule
        if data.quantity > ticket.available_quantity:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {ticket.available_quantity} tickets remain available in this category."
            )

        subtotal = ticket.price * data.quantity
        tax = subtotal * TAX_RATE
        discount = Decimal("0.00")
        total_amount = subtotal + tax - discount

        from app.models.purchase import Purchase, PurchaseStatus

        purchase = Purchase(
            registration_id=data.registration_id,
            ticket_id=ticket_id,
            quantity=data.quantity,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            total_amount=total_amount,
            status=PurchaseStatus.PENDING
        )

        purchase_repo.add(purchase)

        db.flush()

        # reserve the tickets immediately at purchase creation, not
        # waiting for payment - prevents 2 people from both "purchasing"
        # the same last remaining ticket while one is still mid-payment
        ticket.available_quantity -= data.quantity

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Purchase",
            entity_id=purchase.id,
            description=f"Purchase of {data.quantity} x {ticket.ticket_type} created, total {total_amount}"
        )

        db.commit()

        purchase = purchase_repo.get_by_id_with_details(purchase.id)

        logger.info(f"Purchase created successfully : {purchase.id}")

        return {"message": "Purchase created successfully.", "data": purchase}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Purchase creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create purchase.")


def get_purchase_by_id(purchase_id: int, db: Session) -> dict:

    purchase_repo = PurchaseRepository(db)

    purchase = purchase_repo.get_by_id_with_details(purchase_id)

    if not purchase:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found.")

    return {"message": "Purchase fetched successfully.", "data": purchase}