from datetime import datetime

from pydantic import Field, model_validator

from app.models.event import EventStatus, EventType
from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.user_schema import UserBasicResponse


class EventCreate(AppBaseSchema):
    event_name: str = Field(..., min_length=3, max_length=200)
    description: str | None = Field(None, max_length=2000)
    event_type: EventType
    start_date: datetime
    end_date: datetime
    registration_start: datetime
    registration_end: datetime
    capacity: int = Field(..., gt=0)

    # end date must be after start date, registration closing date
    # cannot be after event start date - level 2's own business rules,
    # matching the database's check constraints
    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date.")
        if self.registration_end > self.start_date:
            raise ValueError("registration_end cannot be after start_date.")
        if self.registration_start >= self.registration_end:
            raise ValueError("registration_start must be before registration_end.")
        return self


class EventUpdate(AppBaseSchema):
    event_name: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=2000)
    end_date: datetime | None = None
    registration_end: datetime | None = None
    capacity: int | None = Field(None, gt=0)
    status: EventStatus | None = None


class EventBasicResponse(AppBaseSchema):
    id: int
    event_name: str
    event_type: EventType
    status: EventStatus


class EventResponse(EventBasicResponse):
    description: str | None
    organizer: UserBasicResponse
    start_date: datetime
    end_date: datetime
    registration_start: datetime
    registration_end: datetime
    capacity: int
    created_at: datetime
    updated_at: datetime


class EventMessageResponse(AppBaseSchema):
    message: str
    data: EventResponse


class EventPaginationResponse(AppBaseSchema):
    message: str
    data: list[EventResponse]
    pagination: PaginationResponse