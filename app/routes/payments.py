from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.permissions import require_any_role
from app.database import get_db
from app.models.user import User
from app.schemas.payment_schema import PaymentCreate, PaymentMessageResponse
from app.schemas.purchase_schema import PurchaseCreate, PurchaseMessageResponse
from app.services.payment_service import create_payment, confirm_payment, get_payment_by_id
from app.services.purchase_service import create_purchase, get_purchase_by_id

from datetime import datetime
from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.payment_schema import PaymentPaginationResponse
from app.services.payment_service import get_all_payments

from fastapi import Query

router = APIRouter(prefix="/api/v1", tags=["Ticket Purchase & Payment"])


@router.post("/tickets/{ticket_id}/purchase", response_model=PurchaseMessageResponse, status_code=status.HTTP_201_CREATED)
def purchase_ticket(ticket_id: int, data: PurchaseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return create_purchase(ticket_id, data, current_user, db)


@router.get("/purchases/{purchase_id}", response_model=PurchaseMessageResponse, dependencies=[Depends(require_any_role)])
def get_purchase(purchase_id: int, db: Session = Depends(get_db)):

    return get_purchase_by_id(purchase_id, db)


@router.post("/payments/{purchase_id}", response_model=PaymentMessageResponse, status_code=status.HTTP_201_CREATED)
def pay_for_purchase(purchase_id: int, data: PaymentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return create_payment(purchase_id, data, current_user, db)


@router.patch("/payments/{payment_id}/status", response_model=PaymentMessageResponse)
def update_payment_status(payment_id: int, is_success: bool, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return confirm_payment(payment_id, is_success, current_user, db)


@router.get("/payments/{payment_id}", response_model=PaymentMessageResponse, dependencies=[Depends(require_any_role)])
def get_payment(payment_id: int, db: Session = Depends(get_db)):

    return get_payment_by_id(payment_id, db)


@router.get("/payments", response_model=PaymentPaginationResponse, dependencies=[Depends(require_any_role)])
def list_payments(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    payment_status: PaymentStatus | None = Query(None, alias="status"),
    payment_method: PaymentMethod | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: Session = Depends(get_db)
):

    return get_all_payments(db=db, page=page, limit=limit, payment_status=payment_status, payment_method=payment_method, start_date=start_date, end_date=end_date)