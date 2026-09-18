from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.ticket import Ticket
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket_schema import TicketCreate, TicketUpdate
from app.utils.logger import logger


def create_ticket(event_id: int, data: TicketCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating ticket : event {event_id}, type {data.ticket_type}")

        event_repo = BaseRepository(Event, db)
        ticket_repo = TicketRepository(db)
        audit_repo = AuditLogRepository(db)

        event = event_repo.get_by_id(event_id)

        if not event:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

        ticket = Ticket(
            event_id=event_id,
            ticket_type=data.ticket_type,
            price=data.price,
            quantity=data.quantity,
            available_quantity=data.quantity,
            sale_start=data.sale_start,
            sale_end=data.sale_end
        )

        ticket_repo.add(ticket)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Ticket",
            entity_id=ticket.id,
            description=f"Ticket category '{data.ticket_type}' created for event {event_id}"
        )

        db.commit()

        db.refresh(ticket)

        logger.info(f"Ticket created successfully : {ticket.id}")

        return {"message": "Ticket category created successfully.", "data": ticket}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Ticket creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create ticket category.")


def get_tickets_for_event(event_id: int, db: Session) -> dict:

    ticket_repo = TicketRepository(db)

    tickets = ticket_repo.list_for_event(event_id)

    return {"message": "Tickets fetched successfully.", "data": tickets}


def update_ticket(ticket_id: int, data: TicketUpdate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Updating ticket : {ticket_id}")

        ticket_repo = TicketRepository(db)
        audit_repo = AuditLogRepository(db)

        ticket = ticket_repo.get_by_id(ticket_id)

        if not ticket:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket category not found.")

        update_data = data.model_dump(exclude_unset=True)

        # if quantity is being reduced, make sure it never drops below
        # what's already been sold (quantity - available_quantity)
        if "quantity" in update_data:

            already_sold = ticket.quantity - ticket.available_quantity

            if update_data["quantity"] < already_sold:

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Quantity cannot be reduced below {already_sold}, the number already sold."
                )

            # keep available_quantity consistent with the new total
            ticket.available_quantity = update_data["quantity"] - already_sold

        for key, value in update_data.items():

            setattr(ticket, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Ticket",
            entity_id=ticket.id,
            description="Ticket category updated"
        )

        db.commit()

        db.refresh(ticket)

        logger.info(f"Ticket updated successfully : {ticket_id}")

        return {"message": "Ticket category updated successfully.", "data": ticket}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Ticket update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update ticket category.")