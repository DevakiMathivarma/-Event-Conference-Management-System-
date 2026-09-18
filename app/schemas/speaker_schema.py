# app/schemas/speaker_schema.py

from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.user_schema import UserBasicResponse


# creates both the login account and the speaker profile together, in
# one call - same combined pattern as tenant/customer across every
# previous project. created by an event organizer, not self-registered,
# matching our earlier confirmed decision
class SpeakerCreate(AppBaseSchema):
    full_name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8, max_length=100)
    bio: str | None = Field(None, max_length=2000)
    expertise: str | None = Field(None, max_length=300)
    company: str | None = Field(None, max_length=200)
    experience: int | None = Field(None, ge=0, le=80)


class SpeakerUpdate(AppBaseSchema):
    bio: str | None = Field(None, max_length=2000)
    expertise: str | None = Field(None, max_length=300)
    company: str | None = Field(None, max_length=200)
    experience: int | None = Field(None, ge=0, le=80)

    # is_active here refers to availability for new assignments, not
    # the login account itself - genuinely separate concepts, same
    # distinction we made at the model stage
    is_active: bool | None = None


class SpeakerBasicResponse(AppBaseSchema):
    id: int
    user: UserBasicResponse
    expertise: str | None
    is_active: bool


class SpeakerResponse(SpeakerBasicResponse):
    bio: str | None
    company: str | None
    experience: int | None
    created_by: UserBasicResponse | None
    created_at: datetime
    updated_at: datetime


class SpeakerMessageResponse(AppBaseSchema):
    message: str
    data: SpeakerResponse


class SpeakerPaginationResponse(AppBaseSchema):
    message: str
    data: list[SpeakerResponse]
    pagination: PaginationResponse