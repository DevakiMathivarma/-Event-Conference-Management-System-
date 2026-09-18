from datetime import datetime

from pydantic import Field

from app.models.check_in import CheckInMethod
from app.schemas.common_schema import AppBaseSchema
from app.schemas.user_schema import UserBasicResponse


class CheckInRequest(AppBaseSchema):
    check_in_method: CheckInMethod = CheckInMethod.MANUAL


class CheckOutRequest(AppBaseSchema):
    pass


class CheckInResponse(AppBaseSchema):
    id: int
    registration_id: int
    check_in_time: datetime | None
    check_out_time: datetime | None
    check_in_method: CheckInMethod | None
    checked_in_by: UserBasicResponse | None


class CheckInMessageResponse(AppBaseSchema):
    message: str
    data: CheckInResponse


class AttendanceListResponse(AppBaseSchema):
    message: str
    data: list[CheckInResponse]


# used specifically by the qr verification result - a lighter response,
# since the client scanning a qr code mainly needs a quick yes/no plus
# who it belongs to, not the full check-in record shape
class QRVerificationResult(AppBaseSchema):
    registration_id: int
    attendee_name: str
    event_name: str
    is_valid: bool
    message: str