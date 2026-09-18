# app/models/__init__.py

# importing every model here ensures they're all registered with
# SQLAlchemy's mapper registry before any mapper configuration happens -
# a real bug we hit in the property platform, where a model referenced
# only by string name inside a relationship (not directly imported
# anywhere) caused a mapper resolution failure under pytest
from app.models.user import User
from app.models.event import Event
from app.models.venue import Venue
from app.models.hall import Hall
from app.models.speaker import Speaker
from app.models.session import Session
from app.models.attendee import Attendee
from app.models.registration import Registration
from app.models.ticket import Ticket
from app.models.purchase import Purchase
from app.models.payment import Payment
from app.models.session_booking import SessionBooking
from app.models.check_in import CheckIn
from app.models.certificate import Certificate
from app.models.feedback import Feedback
from app.models.refund import Refund
from app.models.audit_log import AuditLog