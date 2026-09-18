from datetime import datetime

from pydantic import Field

from app.models.certificate import CertificateStatus, CertificateType
from app.schemas.common_schema import AppBaseSchema
from app.schemas.attendee_schema import AttendeeBasicResponse
from app.schemas.event_schema import EventBasicResponse


class CertificateGenerate(AppBaseSchema):
    certificate_type: CertificateType = CertificateType.PARTICIPATION


class CertificateResponse(AppBaseSchema):
    id: int
    certificate_number: str
    attendee: AttendeeBasicResponse
    event: EventBasicResponse
    issue_date: datetime
    certificate_type: CertificateType
    status: CertificateStatus


class CertificateMessageResponse(AppBaseSchema):
    message: str
    data: CertificateResponse


class CertificateListResponse(AppBaseSchema):
    message: str
    data: list[CertificateResponse]