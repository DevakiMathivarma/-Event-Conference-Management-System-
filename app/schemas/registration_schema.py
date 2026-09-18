from datetime import datetime

from pydantic import Field

from app.models.registration import RegistrationStatus
from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.attendee_schema import AttendeeBasicResponse
from app.schemas.event_schema import EventBasicResponse


class RegistrationCreate(AppBaseSchema):
    # deliberately empty - event_id comes from the url, attendee_id
    # comes from whoever's logged in, same "ownership from the token,
    # not the client" principle used throughout every project. nothing
    # else needs to be supplied by the client at all to register
    pass


class RegistrationBasicResponse(AppBaseSchema):
    id: int
    registration_status: RegistrationStatus


class RegistrationResponse(RegistrationBasicResponse):
    attendee: AttendeeBasicResponse
    event: EventBasicResponse
    registration_date: datetime


class RegistrationMessageResponse(AppBaseSchema):
    message: str
    data: RegistrationResponse


class RegistrationPaginationResponse(AppBaseSchema):
    message: str
    data: list[RegistrationResponse]
    pagination: PaginationResponse