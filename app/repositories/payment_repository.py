# app/repositories/payment_repository.py

from sqlalchemy.orm import Session, joinedload

from app.models.payment import Payment
from app.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Payment, db)

    def get_by_id_with_details(self, payment_id: int):

        return self.db.query(Payment).options(joinedload(Payment.purchase)).filter(Payment.id == payment_id).first()

    def get_by_purchase_id(self, purchase_id: int):

        return self.db.query(Payment).filter(Payment.purchase_id == purchase_id).first()

    def list_payments(self, payment_status, payment_method, start_date, end_date, sort_column, sort_order, offset, limit):

        query = self.db.query(Payment).options(joinedload(Payment.purchase))

        if payment_status:

            query = query.filter(Payment.payment_status == payment_status)

        if payment_method:

            query = query.filter(Payment.payment_method == payment_method)

        if start_date:

            query = query.filter(Payment.payment_date >= start_date)

        if end_date:

            query = query.filter(Payment.payment_date <= end_date)

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        payments = query.offset(offset).limit(limit).all()

        return payments, total_records