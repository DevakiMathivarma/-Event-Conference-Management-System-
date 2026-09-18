from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin_or_organizer, require_any_role
from app.database import get_db
from app.models.user import User
from app.schemas.ticket_schema import TicketCreate, TicketUpdate, TicketMessageResponse, TicketListResponse
from app.services.ticket_service import create_ticket, get_tickets_for_event, update_ticket

router = APIRouter(prefix="/api/v1", tags=["Ticket Management"])


@router.post("/events/{event_id}/tickets", response_model=TicketMessageResponse, status_code=status.HTTP_201_CREATED)
def create_new_ticket(event_id: int, data: TicketCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return create_ticket(event_id, data, current_user, db)


@router.get("/events/{event_id}/tickets", response_model=TicketListResponse, dependencies=[Depends(require_any_role)])
def list_event_tickets(event_id: int, db: Session = Depends(get_db)):

    return get_tickets_for_event(event_id, db)


@router.put("/tickets/{ticket_id}", response_model=TicketMessageResponse)
def update_existing_ticket(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_organizer)):

    return update_ticket(ticket_id, data, current_user, db)