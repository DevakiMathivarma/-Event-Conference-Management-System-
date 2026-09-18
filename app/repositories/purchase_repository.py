from sqlalchemy.orm import Session, joinedload

from app.models.purchase import Purchase
from app.repositories.base_repository import BaseRepository


class PurchaseRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Purchase, db)

    def get_by_id_with_details(self, purchase_id: int):

        return (
            self.db.query(Purchase)
            .options(joinedload(Purchase.registration), joinedload(Purchase.ticket))
            .filter(Purchase.id == purchase_id)
            .first()
        )