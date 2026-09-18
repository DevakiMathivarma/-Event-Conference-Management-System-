from decimal import Decimal

from app.schemas.common_schema import AppBaseSchema


class OrganizerDashboardSummary(AppBaseSchema):
    total_registrations: int
    confirmed_registrations: int
    pending_registrations: int
    cancelled_registrations: int
    total_revenue: Decimal
    tickets_sold: int
    total_session_bookings: int
    average_rating: float | None
    total_check_ins: int


class OrganizerDashboardResponse(AppBaseSchema):
    message: str
    data: OrganizerDashboardSummary


class AdminDashboardSummary(AppBaseSchema):
    total_events: int
    active_events: int
    completed_events: int
    total_attendees: int
    total_speakers: int
    total_registrations: int
    total_tickets_sold: int
    total_revenue: Decimal
    total_refunds: Decimal
    upcoming_events: int
    average_event_rating: float | None
    cancellation_rate: float


class AdminDashboardResponse(AppBaseSchema):
    message: str
    data: AdminDashboardSummary


class TopEventEntry(AppBaseSchema):
    event_id: int
    event_name: str
    total_registrations: int
    total_revenue: Decimal


class TopEventsResponse(AppBaseSchema):
    message: str
    data: list[TopEventEntry]


class TopSpeakerEntry(AppBaseSchema):
    speaker_id: int
    speaker_name: str
    average_rating: float
    total_sessions: int


class TopSpeakersResponse(AppBaseSchema):
    message: str
    data: list[TopSpeakerEntry]


class MonthlyRegistrationEntry(AppBaseSchema):
    month: str
    registration_count: int


class MonthlyRegistrationsResponse(AppBaseSchema):
    message: str
    data: list[MonthlyRegistrationEntry]


class MonthlyRevenueEntry(AppBaseSchema):
    month: str
    total_revenue: Decimal


class MonthlyRevenueResponse(AppBaseSchema):
    message: str
    data: list[MonthlyRevenueEntry]

# add these to the existing file

class DailyRegistrationEntry(AppBaseSchema):
    date: str
    registration_count: int

class DailyRegistrationsResponse(AppBaseSchema):
    message: str
    data: list[DailyRegistrationEntry]


class TicketSalesEntry(AppBaseSchema):
    ticket_type: str
    quantity_sold: int
    revenue: Decimal

class TicketSalesResponse(AppBaseSchema):
    message: str
    data: list[TicketSalesEntry]


class AttendanceReportEntry(AppBaseSchema):
    attendee_name: str
    check_in_time: str | None
    check_out_time: str | None
    check_in_method: str | None

class AttendanceReportResponse(AppBaseSchema):
    message: str
    data: list[AttendanceReportEntry]


class SessionPopularityEntry(AppBaseSchema):
    session_id: int
    session_title: str
    total_bookings: int
    capacity: int

class SessionPopularityResponse(AppBaseSchema):
    message: str
    data: list[SessionPopularityEntry]