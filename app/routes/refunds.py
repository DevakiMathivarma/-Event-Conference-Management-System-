from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin, require_any_role
from app.database import get_db
from app.models.user import User
from app.schemas.refund_schema import RefundCreate, RefundMessageResponse, RefundPaginationResponse
from app.services.refund_service import create_refund, get_refund_by_id, get_all_refunds

router = APIRouter(prefix="/api/v1", tags=["Refund Management"])


@router.post("/purchases/{purchase_id}/refund", response_model=RefundMessageResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def process_refund(purchase_id: int, data: RefundCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    return create_refund(purchase_id, data, current_user, db)


@router.get("/refunds", response_model=RefundPaginationResponse, dependencies=[Depends(require_any_role)])
def list_refunds(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):

    return get_all_refunds(db, page, limit)


@router.get("/refunds/{refund_id}", response_model=RefundMessageResponse, dependencies=[Depends(require_any_role)])
def get_refund(refund_id: int, db: Session = Depends(get_db)):

    return get_refund_by_id(refund_id, db)