from app.celery_app import celery_app
from app.database import SessionLocal
from app.utils.email import send_email
from app.utils.logger import logger

EVENT_REMINDER_WINDOW_DAYS = 3
SESSION_REMINDER_WINDOW_HOURS = 24


@celery_app.task(name="app.tasks.send_email_task")
def send_email_task(to_email: str, subject: str, body: str, attachment_paths: list[str] | None = None) -> None:

    try:

        send_email(to_email=to_email, subject=subject, body=body, attachment_paths=attachment_paths)

        logger.info(f"Celery task - email sent to {to_email} : {subject}")

    except Exception as error:

        logger.error(f"Celery task - email failed to {to_email} : {str(error)}")


@celery_app.task(name="app.tasks.send_registration_confirmation_email")
def send_registration_confirmation_email(to_email: str, attendee_name: str, event_name: str) -> None:

    body = f"Hi {attendee_name},\n\nYou're registered for {event_name}. We look forward to seeing you there!"

    send_email_task(to_email, "Registration Confirmed", body)


@celery_app.task(name="app.tasks.send_payment_success_email")
def send_payment_success_email(to_email: str, attendee_name: str, amount: str, event_name: str) -> None:

    body = f"Hi {attendee_name},\n\nWe've received your payment of {amount} for {event_name}."

    send_email_task(to_email, "Payment Successful", body)


@celery_app.task(name="app.tasks.send_ticket_confirmation_email")
def send_ticket_confirmation_email(to_email: str, attendee_name: str, event_name: str, ticket_path: str | None = None) -> None:

    body = f"Hi {attendee_name},\n\nYour ticket for {event_name} is confirmed. Your ticket is attached."

    attachments = [ticket_path] if ticket_path else []

    send_email_task(to_email, "Ticket Confirmed", body, attachment_paths=attachments)


@celery_app.task(name="app.tasks.send_certificate_availability_email")
def send_certificate_availability_email(to_email: str, attendee_name: str, event_name: str, certificate_path: str | None = None) -> None:

    body = f"Hi {attendee_name},\n\nYour certificate for {event_name} is now available. It's attached to this email."

    attachments = [certificate_path] if certificate_path else []

    send_email_task(to_email, "Certificate Available", body, attachment_paths=attachments)


@celery_app.task(name="app.tasks.send_event_cancellation_email")
def send_event_cancellation_email(to_email: str, attendee_name: str, event_name: str) -> None:

    body = f"Hi {attendee_name},\n\nWe're sorry to let you know that {event_name} has been cancelled. A refund will be processed automatically."

    send_email_task(to_email, "Event Cancelled", body)


@celery_app.task(name="app.tasks.send_refund_email")
def send_refund_email(to_email: str, attendee_name: str, event_name: str, refund_amount: str) -> None:

    body = f"Hi {attendee_name},\n\nYour refund of {refund_amount} for {event_name} has been processed."

    send_email_task(to_email, "Refund Processed", body)


@celery_app.task(name="app.tasks.send_event_reminder_email")
def send_event_reminder_email(to_email: str, attendee_name: str, event_name: str, start_date: str) -> None:

    body = f"Hi {attendee_name},\n\nJust a reminder - {event_name} starts on {start_date}. We look forward to seeing you there!"

    send_email_task(to_email, "Event Reminder", body)


@celery_app.task(name="app.tasks.send_session_reminder_email")
def send_session_reminder_email(to_email: str, attendee_name: str, session_title: str, start_time: str) -> None:

    body = f"Hi {attendee_name},\n\nReminder - the session '{session_title}' you booked starts at {start_time}."

    send_email_task(to_email, "Session Reminder", body)

@celery_app.task(name="app.tasks.run_daily_reminder_checks")
def run_daily_reminder_checks() -> None:

    from app.repositories.event_repository import EventRepository
    from app.repositories.session_repository import SessionRepository
    from app.models.registration import Registration, RegistrationStatus
    from app.models.session_booking import SessionBooking

    db = SessionLocal()

    try:

        event_repo = EventRepository(db)
        session_repo = SessionRepository(db)

        upcoming_events = event_repo.get_events_starting_within(EVENT_REMINDER_WINDOW_DAYS)

        event_reminder_count = 0

        for event in upcoming_events:

            confirmed_registrations = (
                db.query(Registration)
                .filter(Registration.event_id == event.id, Registration.registration_status == RegistrationStatus.CONFIRMED)
                .all()
            )

            for registration in confirmed_registrations:

                attendee_user = registration.attendee.user

                send_event_reminder_email.delay(attendee_user.email, attendee_user.full_name, event.event_name, str(event.start_date))

                event_reminder_count += 1

        # session reminders - now genuinely wired, using the new
        # get_sessions_starting_within() method. only notifies
        # attendees who actually booked this specific session, not
        # everyone registered for the whole event
        upcoming_sessions = session_repo.get_sessions_starting_within(SESSION_REMINDER_WINDOW_HOURS)

        session_reminder_count = 0

        for session in upcoming_sessions:

            bookings = db.query(SessionBooking).filter(SessionBooking.session_id == session.id).all()

            for booking in bookings:

                attendee_user = booking.registration.attendee.user

                send_session_reminder_email.delay(attendee_user.email, attendee_user.full_name, session.title, str(session.start_time))

                session_reminder_count += 1

        logger.info(f"Daily reminder checks complete : {event_reminder_count} event reminders, {session_reminder_count} session reminders sent")

    except Exception as error:

        logger.error(f"Daily reminder check failed : {str(error)}")

    finally:

        db.close()