from datetime import datetime
from decimal import Decimal

from pydantic import Field, model_validator

from app.schemas.common_schema import AppBaseSchema, PaginationResponse


class TicketCreate(AppBaseSchema):
    ticket_type: str = Field(..., pattern="^(STANDARD|VIP|EARLY_BIRD|STUDENT)$")
    price: Decimal = Field(..., ge=0)
    quantity: int = Field(..., ge=0)
    sale_start: datetime
    sale_end: datetime

    @model_validator(mode="after")
    def check_sale_dates(self):
        if self.sale_end <= self.sale_start:
            raise ValueError("sale_end must be after sale_start.")
        return self


class TicketUpdate(AppBaseSchema):
    price: Decimal | None = Field(None, ge=0)
    quantity: int | None = Field(None, ge=0)
    sale_start: datetime | None = None
    sale_end: datetime | None = None


class TicketResponse(AppBaseSchema):
    id: int
    event_id: int
    ticket_type: str
    price: Decimal
    quantity: int
    available_quantity: int
    sale_start: datetime
    sale_end: datetime
    created_at: datetime
    updated_at: datetime


class TicketMessageResponse(AppBaseSchema):
    message: str
    data: TicketResponse


class TicketListResponse(AppBaseSchema):
    message: str
    data: list[TicketResponse]