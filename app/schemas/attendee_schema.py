from datetime import datetime
from pydantic import EmailStr, Field

from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.user_schema import UserBasicResponse


# creates both the login account and the attendee profile together, in
# one call - purely self-service, no hybrid staff-created path, same
# confirmed reasoning as customer/delivery partner in the food delivery
# platform
class AttendeeCreate(AppBaseSchema):
    full_name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8, max_length=100)
    organization: str | None = Field(None, max_length=200)
    designation: str | None = Field(None, max_length=150)


class AttendeeUpdate(AppBaseSchema):
    full_name: str | None = Field(None, min_length=3, max_length=100)
    phone: str | None = Field(None, min_length=10, max_length=15)
    organization: str | None = Field(None, max_length=200)
    designation: str | None = Field(None, max_length=150)


class AttendeeBasicResponse(AppBaseSchema):
    id: int
    user: UserBasicResponse


class AttendeeResponse(AttendeeBasicResponse):
    organization: str | None
    designation: str | None
    created_at: datetime
    updated_at: datetime


class AttendeeMessageResponse(AppBaseSchema):
    message: str
    data: AttendeeResponse


class AttendeePaginationResponse(AppBaseSchema):
    message: str
    data: list[AttendeeResponse]
    pagination: PaginationResponse