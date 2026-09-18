from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.check_in import CheckIn
from app.models.event import Event
from app.models.feedback import Feedback
from app.models.payment import Payment, PaymentStatus
from app.models.purchase import Purchase
from app.models.registration import Registration, RegistrationStatus
from app.schemas.dashboard_schema import OrganizerDashboardSummary
from app.utils.logger import logger


def get_organizer_dashboard(event_id: int, current_user, db: Session) -> dict:

    logger.info(f"Generating organizer dashboard for event : {event_id}")

    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    if current_user.role.value == "EVENT_ORGANIZER" and event.organizer_id != current_user.id:

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own event's dashboard.")

    registrations = db.query(Registration).filter(Registration.event_id == event_id).all()

    confirmed = [r for r in registrations if r.registration_status == RegistrationStatus.CONFIRMED]
    pending = [r for r in registrations if r.registration_status == RegistrationStatus.PENDING]
    cancelled = [r for r in registrations if r.registration_status == RegistrationStatus.CANCELLED]

    registration_ids = [r.id for r in registrations]

    total_revenue = Decimal("0.00")
    tickets_sold = 0

    if registration_ids:

        purchases = db.query(Purchase).filter(Purchase.registration_id.in_(registration_ids)).all()

        purchase_ids = [p.id for p in purchases]

        tickets_sold = sum(p.quantity for p in purchases)

        if purchase_ids:

            payments = db.query(Payment).filter(Payment.purchase_id.in_(purchase_ids), Payment.payment_status == PaymentStatus.SUCCESS).all()

            total_revenue = sum((p.amount for p in payments), Decimal("0.00"))

    # session bookings - the missing organizer-dashboard metric, now added
    from app.models.session import Session as SessionModel
    from app.models.session_booking import SessionBooking

    event_session_ids = [s.id for s in db.query(SessionModel.id).filter(SessionModel.event_id == event_id).all()]

    total_session_bookings = 0

    if event_session_ids:

        total_session_bookings = db.query(SessionBooking).filter(SessionBooking.session_id.in_(event_session_ids)).count()

    ratings = [f.rating for f in db.query(Feedback).filter(Feedback.event_id == event_id).all()]

    average_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    total_check_ins = 0

    if registration_ids:

        total_check_ins = db.query(CheckIn).filter(CheckIn.registration_id.in_(registration_ids), CheckIn.check_in_time.isnot(None)).count()

    summary = OrganizerDashboardSummary(
        total_registrations=len(registrations),
        confirmed_registrations=len(confirmed),
        pending_registrations=len(pending),
        cancelled_registrations=len(cancelled),
        total_revenue=total_revenue,
        tickets_sold=tickets_sold,
        total_session_bookings=total_session_bookings,
        average_rating=average_rating,
        total_check_ins=total_check_ins
    )

    return {"message": "Organizer dashboard generated successfully.", "data": summary}