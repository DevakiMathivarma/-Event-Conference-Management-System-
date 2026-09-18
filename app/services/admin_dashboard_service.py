# app/services/admin_dashboard_service.py

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.models.attendee import Attendee
from app.models.event import Event, EventStatus
from app.models.feedback import Feedback
from app.models.payment import Payment, PaymentStatus
from app.models.purchase import Purchase
from app.models.refund import Refund
from app.models.registration import Registration
from app.models.speaker import Speaker
from app.schemas.dashboard_schema import (
    AdminDashboardSummary, TopEventEntry, TopSpeakerEntry, MonthlyRegistrationEntry, MonthlyRevenueEntry,
    DailyRegistrationEntry, TicketSalesEntry, SessionPopularityEntry
)
from app.utils.logger import logger

TOP_LIMIT = 10


def get_admin_dashboard(db: Session) -> dict:

    logger.info("Generating admin dashboard.")

    total_events = db.query(Event).count()
    active_events = db.query(Event).filter(Event.status.in_([EventStatus.PUBLISHED, EventStatus.REGISTRATION_OPEN, EventStatus.REGISTRATION_CLOSED])).count()
    completed_events = db.query(Event).filter(Event.status == EventStatus.COMPLETED).count()

    total_attendees = db.query(Attendee).count()
    total_speakers = db.query(Speaker).count()

    total_registrations = db.query(Registration).count()

    all_purchases = db.query(Purchase).all()
    total_tickets_sold = sum(p.quantity for p in all_purchases)

    successful_payments = db.query(Payment.amount).filter(Payment.payment_status == PaymentStatus.SUCCESS).all()
    total_revenue = sum((row[0] for row in successful_payments), Decimal("0.00"))

    refund_amounts = db.query(Refund.refund_amount).all()
    total_refunds = sum((row[0] for row in refund_amounts), Decimal("0.00"))

    today = date.today()
    cutoff = today + timedelta(days=30)

    upcoming_events = db.query(Event).filter(Event.start_date >= today, Event.start_date <= cutoff).count()

    ratings = [f.rating for f in db.query(Feedback).all()]
    average_event_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    cancelled_registrations = db.query(Registration).filter(Registration.registration_status == "CANCELLED").count()
    cancellation_rate = round((cancelled_registrations / total_registrations) * 100, 2) if total_registrations > 0 else 0.0

    summary = AdminDashboardSummary(
        total_events=total_events,
        active_events=active_events,
        completed_events=completed_events,
        total_attendees=total_attendees,
        total_speakers=total_speakers,
        total_registrations=total_registrations,
        total_tickets_sold=total_tickets_sold,
        total_revenue=total_revenue,
        total_refunds=total_refunds,
        upcoming_events=upcoming_events,
        average_event_rating=average_event_rating,
        cancellation_rate=cancellation_rate
    )

    return {"message": "Admin dashboard generated successfully.", "data": summary}


# daily registration report - level 15's own named report
def get_daily_registrations_report(db: Session) -> dict:

    registrations = db.query(Registration).all()

    daily = defaultdict(int)

    for registration in registrations:

        day_key = registration.registration_date.strftime("%Y-%m-%d")
        daily[day_key] += 1

    data = [DailyRegistrationEntry(date=day, registration_count=count) for day, count in sorted(daily.items())]

    return {"message": "Daily registration report generated successfully.", "data": data}


# ticket sales report - level 15's own named report
def get_ticket_sales_report(db: Session) -> dict:

    purchases = db.query(Purchase).options(joinedload(Purchase.ticket)).all()

    sales = defaultdict(lambda: {"quantity": 0, "revenue": Decimal("0.00")})

    for purchase in purchases:

        if purchase.status.value == "CONFIRMED":

            sales[purchase.ticket.ticket_type]["quantity"] += purchase.quantity
            sales[purchase.ticket.ticket_type]["revenue"] += purchase.total_amount

    data = [TicketSalesEntry(ticket_type=t, quantity_sold=v["quantity"], revenue=v["revenue"]) for t, v in sales.items()]

    return {"message": "Ticket sales report generated successfully.", "data": data}


# session popularity report - level 15's own named report
def get_session_popularity_report(db: Session) -> dict:

    from app.models.session import Session as SessionModel
    from app.models.session_booking import SessionBooking

    sessions = db.query(SessionModel).all()

    booking_counts = defaultdict(int)

    for session_id, in db.query(SessionBooking.session_id).all():

        booking_counts[session_id] += 1

    ranked = sorted(sessions, key=lambda s: booking_counts[s.id], reverse=True)[:TOP_LIMIT]

    data = [
        SessionPopularityEntry(session_id=s.id, session_title=s.title, total_bookings=booking_counts[s.id], capacity=s.capacity)
        for s in ranked
    ]

    return {"message": "Session popularity report generated successfully.", "data": data}


def get_top_events_report(db: Session) -> dict:

    events = db.query(Event).all()

    registration_counts = defaultdict(int)

    for event_id, in db.query(Registration.event_id).all():

        registration_counts[event_id] += 1

    revenue_by_event = defaultdict(lambda: Decimal("0.00"))

    rows = (
        db.query(Registration.event_id, Payment.amount)
        .select_from(Payment)
        .join(Purchase, Payment.purchase_id == Purchase.id)
        .join(Registration, Purchase.registration_id == Registration.id)
        .filter(Payment.payment_status == PaymentStatus.SUCCESS)
        .all()
    )

    for event_id, amount in rows:

        revenue_by_event[event_id] += amount

    ranked = sorted(events, key=lambda e: revenue_by_event[e.id], reverse=True)[:TOP_LIMIT]

    data = [
        TopEventEntry(event_id=e.id, event_name=e.event_name, total_registrations=registration_counts[e.id], total_revenue=revenue_by_event[e.id])
        for e in ranked
    ]

    return {"message": "Top events report generated successfully.", "data": data}


def get_top_speakers_report(db: Session) -> dict:

    speakers = db.query(Speaker).options(joinedload(Speaker.user)).all()

    ratings_by_speaker = defaultdict(list)

    for speaker_id, rating in db.query(Feedback.speaker_id, Feedback.rating).filter(Feedback.speaker_id.isnot(None)).all():

        ratings_by_speaker[speaker_id].append(rating)

    session_counts = defaultdict(int)

    from app.models.session import Session as SessionModel

    for speaker_id, in db.query(SessionModel.speaker_id).filter(SessionModel.speaker_id.isnot(None)).all():

        session_counts[speaker_id] += 1

    scored = []

    for speaker in speakers:

        ratings = ratings_by_speaker.get(speaker.id, [])

        if not ratings:

            continue

        average = sum(ratings) / len(ratings)

        scored.append((speaker, average))

    ranked = sorted(scored, key=lambda pair: pair[1], reverse=True)[:TOP_LIMIT]

    data = [
        TopSpeakerEntry(speaker_id=speaker.id, speaker_name=speaker.user.full_name, average_rating=round(avg, 2), total_sessions=session_counts[speaker.id])
        for speaker, avg in ranked
    ]

    return {"message": "Top speakers report generated successfully.", "data": data}


def get_monthly_registrations_report(db: Session) -> dict:

    registrations = db.query(Registration).all()

    monthly = defaultdict(int)

    for registration in registrations:

        month_key = registration.registration_date.strftime("%Y-%m")

        monthly[month_key] += 1

    data = [MonthlyRegistrationEntry(month=month, registration_count=count) for month, count in sorted(monthly.items())]

    return {"message": "Monthly registrations report generated successfully.", "data": data}


def get_monthly_revenue_report(db: Session) -> dict:

    successful_payments = db.query(Payment).filter(Payment.payment_status == PaymentStatus.SUCCESS).all()

    monthly = defaultdict(lambda: Decimal("0.00"))

    for payment in successful_payments:

        month_key = payment.payment_date.strftime("%Y-%m")

        monthly[month_key] += payment.amount

    data = [MonthlyRevenueEntry(month=month, total_revenue=total) for month, total in sorted(monthly.items())]

    return {"message": "Monthly revenue report generated successfully.", "data": data}

import io
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font


def _build_excel_response(filename: str, headers: list[str], rows: list[list]) -> StreamingResponse:

    workbook = Workbook()

    sheet = workbook.active

    sheet.append(headers)

    for cell in sheet[1]:

        cell.font = Font(bold=True)

    for row in rows:

        sheet.append(row)

    buffer = io.BytesIO()

    workbook.save(buffer)

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def export_ticket_sales_excel(db: Session) -> StreamingResponse:

    report = get_ticket_sales_report(db)

    rows = [[entry.ticket_type, entry.quantity_sold, float(entry.revenue)] for entry in report["data"]]

    return _build_excel_response("ticket_sales.xlsx", ["Ticket Type", "Quantity Sold", "Revenue"], rows)


def export_daily_registrations_excel(db: Session) -> StreamingResponse:

    report = get_daily_registrations_report(db)

    rows = [[entry.date, entry.registration_count] for entry in report["data"]]

    return _build_excel_response("daily_registrations.xlsx", ["Date", "Registration Count"], rows)