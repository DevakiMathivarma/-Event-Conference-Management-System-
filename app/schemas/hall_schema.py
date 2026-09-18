from datetime import datetime

from pydantic import Field

from app.models.hall import HallAvailabilityStatus
from app.schemas.common_schema import AppBaseSchema


class HallCreate(AppBaseSchema):
    hall_name: str = Field(..., min_length=2, max_length=150)
    capacity: int = Field(..., gt=0)
    floor: int | None = None


class HallUpdate(AppBaseSchema):
    hall_name: str | None = Field(None, min_length=2, max_length=150)
    capacity: int | None = Field(None, gt=0)
    floor: int | None = None
    availability_status: HallAvailabilityStatus | None = None


class HallResponse(AppBaseSchema):
    id: int
    venue_id: int
    hall_name: str
    capacity: int
    floor: int | None
    availability_status: HallAvailabilityStatus
    created_at: datetime
    updated_at: datetime


class HallMessageResponse(AppBaseSchema):
    message: str
    data: HallResponse


class HallListResponse(AppBaseSchema):
    message: str
    data: list[HallResponse]