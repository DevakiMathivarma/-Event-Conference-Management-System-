from datetime import datetime

from pydantic import Field, model_validator

from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.speaker_schema import SpeakerBasicResponse


class SessionCreate(AppBaseSchema):
    event_id: int
    speaker_id: int | None = None
    hall_id: int
    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = Field(None, max_length=2000)
    start_time: datetime
    end_time: datetime
    capacity: int = Field(..., gt=0)
    session_type: str | None = Field(None, max_length=100)

    @model_validator(mode="after")
    def check_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time.")
        return self


class SessionUpdate(AppBaseSchema):
    speaker_id: int | None = None
    hall_id: int | None = None
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=2000)
    start_time: datetime | None = None
    end_time: datetime | None = None
    capacity: int | None = Field(None, gt=0)
    session_type: str | None = Field(None, max_length=100)


class SessionBasicResponse(AppBaseSchema):
    id: int
    title: str
    start_time: datetime
    end_time: datetime


class SessionResponse(SessionBasicResponse):
    event_id: int
    hall_id: int
    speaker: SpeakerBasicResponse | None
    description: str | None
    capacity: int
    session_type: str | None
    created_at: datetime
    updated_at: datetime


class SessionMessageResponse(AppBaseSchema):
    message: str
    data: SessionResponse


class SessionPaginationResponse(AppBaseSchema):
    message: str
    data: list[SessionResponse]
    pagination: PaginationResponse