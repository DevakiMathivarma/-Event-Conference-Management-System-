from datetime import datetime

from pydantic import Field

from app.models.venue import VenueStatus
from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.user_schema import UserBasicResponse


class VenueCreate(AppBaseSchema):
    venue_name: str = Field(..., min_length=2, max_length=200)
    address: str = Field(..., min_length=5, max_length=300)
    city: str = Field(..., min_length=2, max_length=100)
    capacity: int = Field(..., gt=0)
    facilities: str | None = Field(None, max_length=2000)


class VenueUpdate(AppBaseSchema):
    venue_name: str | None = Field(None, min_length=2, max_length=200)
    address: str | None = Field(None, min_length=5, max_length=300)
    city: str | None = Field(None, min_length=2, max_length=100)
    capacity: int | None = Field(None, gt=0)
    facilities: str | None = Field(None, max_length=2000)
    status: VenueStatus | None = None


class VenueBasicResponse(AppBaseSchema):
    id: int
    venue_name: str
    city: str
    capacity: int
    status: VenueStatus


class VenueResponse(VenueBasicResponse):
    address: str
    facilities: str | None
    created_by: UserBasicResponse | None
    created_at: datetime
    updated_at: datetime


class VenueMessageResponse(AppBaseSchema):
    message: str
    data: VenueResponse


class VenuePaginationResponse(AppBaseSchema):
    message: str
    data: list[VenueResponse]
    pagination: PaginationResponse