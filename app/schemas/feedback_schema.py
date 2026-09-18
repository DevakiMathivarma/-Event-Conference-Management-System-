from datetime import datetime

from pydantic import Field, model_validator

from app.schemas.common_schema import AppBaseSchema, PaginationResponse


class FeedbackCreate(AppBaseSchema):
    event_id: int
    speaker_id: int | None = None
    session_id: int | None = None
    rating: int = Field(..., ge=1, le=5)
    feedback: str | None = Field(None, max_length=2000)


class FeedbackResponse(AppBaseSchema):
    id: int
    registration_id: int
    event_id: int
    speaker_id: int | None
    session_id: int | None
    rating: int
    feedback: str | None
    created_at: datetime


class FeedbackMessageResponse(AppBaseSchema):
    message: str
    data: FeedbackResponse


class FeedbackPaginationResponse(AppBaseSchema):
    message: str
    data: list[FeedbackResponse]
    pagination: PaginationResponse