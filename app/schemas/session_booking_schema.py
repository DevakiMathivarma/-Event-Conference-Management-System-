from datetime import datetime

from pydantic import Field

from app.schemas.common_schema import AppBaseSchema
from app.schemas.session_schema import SessionBasicResponse


class SessionBookingCreate(AppBaseSchema):
    # deliberately empty - session_id comes from the url, registration_id
    # is derived from whoever's logged in (looking up their own
    # confirmed registration), same "ownership from the token" principle
    # used throughout every project
    pass


class SessionBookingResponse(AppBaseSchema):
    id: int
    registration_id: int
    session: SessionBasicResponse
    booked_at: datetime


class SessionBookingMessageResponse(AppBaseSchema):
    message: str
    data: SessionBookingResponse


class SessionBookingListResponse(AppBaseSchema):
    message: str
    data: list[SessionBookingResponse]