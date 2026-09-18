from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.models.event import EventStatus
from app.services.refund_service import _calculate_refund_percentage

def test_organizer_cancelled_event_always_full_refund():
    event_start = datetime.now(timezone.utc) - timedelta(days=1)
    cancellation_date = datetime.now(timezone.utc)
    percentage = _calculate_refund_percentage(event_start, cancellation_date, EventStatus.CANCELLED)
    assert percentage == Decimal("1.00")

def test_early_cancellation_full_refund():
    event_start = datetime.now(timezone.utc) + timedelta(days=10)
    cancellation_date = datetime.now(timezone.utc)
    percentage = _calculate_refund_percentage(event_start, cancellation_date, EventStatus.PUBLISHED)
    assert percentage == Decimal("1.00")

def test_near_event_partial_refund():
    event_start = datetime.now(timezone.utc) + timedelta(days=2)
    cancellation_date = datetime.now(timezone.utc)
    percentage = _calculate_refund_percentage(event_start, cancellation_date, EventStatus.PUBLISHED)
    assert percentage == Decimal("0.50")

def test_after_event_started_no_refund():
    event_start = datetime.now(timezone.utc) - timedelta(days=1)
    cancellation_date = datetime.now(timezone.utc)
    percentage = _calculate_refund_percentage(event_start, cancellation_date, EventStatus.PUBLISHED)
    assert percentage == Decimal("0.00")