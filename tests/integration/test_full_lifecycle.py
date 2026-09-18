from datetime import datetime, timedelta, timezone
from tests.conftest import auth_headers


def _create_event_open_now(client, organizer_token):
    now = datetime.now(timezone.utc)
    start = (now + timedelta(days=5)).isoformat()
    end = (now + timedelta(days=6)).isoformat()
    reg_start = (now - timedelta(days=1)).isoformat()
    reg_end = (now + timedelta(days=4)).isoformat()
    event = client.post("/api/v1/events",
        json={"event_name": "TechConf", "event_type": "CONFERENCE", "start_date": start, "end_date": end,
              "registration_start": reg_start, "registration_end": reg_end, "capacity": 100},
        headers=auth_headers(organizer_token)).json()["data"]
    client.put(f"/api/v1/events/{event['id']}", json={"status": "REGISTRATION_OPEN"}, headers=auth_headers(organizer_token))
    return event


def test_full_lifecycle_registration_to_certificate(client, organizer_token, admin_token, attendee_token):
    event = _create_event_open_now(client, organizer_token)

    # duplicate registration blocked
    reg1 = client.post(f"/api/v1/events/{event['id']}/register", headers=auth_headers(attendee_token))
    assert reg1.status_code == 201
    registration = reg1.json()["data"]

    reg2 = client.post(f"/api/v1/events/{event['id']}/register", headers=auth_headers(attendee_token))
    assert reg2.status_code == 400

    # ticket setup
    now = datetime.now(timezone.utc)
    ticket = client.post(f"/api/v1/events/{event['id']}/tickets",
        json={"ticket_type": "STANDARD", "price": 1000.00, "quantity": 10,
              "sale_start": (now - timedelta(days=1)).isoformat(), "sale_end": (now + timedelta(days=3)).isoformat()},
        headers=auth_headers(organizer_token)).json()["data"]

    # purchase
    purchase = client.post(f"/api/v1/tickets/{ticket['id']}/purchase",
        json={"registration_id": registration["id"], "quantity": 1}, headers=auth_headers(attendee_token)).json()["data"]

    # subtotal check: 1000 * 1 = 1000, tax 5% = 50, total = 1050
    assert float(purchase["subtotal"]) == 1000.00
    assert float(purchase["total_amount"]) == 1050.00

    # payment - create (PENDING)
    payment = client.post(f"/api/v1/payments/{purchase['id']}",
        json={"payment_method": "UPI", "transaction_id": "TXNTEST001"}, headers=auth_headers(attendee_token)).json()["data"]
    assert payment["payment_status"] == "PENDING"

    # duplicate transaction id blocked (need a second purchase first)
    purchase2 = client.post(f"/api/v1/tickets/{ticket['id']}/purchase",
        json={"registration_id": registration["id"], "quantity": 1}, headers=auth_headers(attendee_token)).json()["data"]
    dup_txn = client.post(f"/api/v1/payments/{purchase2['id']}",
        json={"payment_method": "UPI", "transaction_id": "TXNTEST001"}, headers=auth_headers(attendee_token))
    assert dup_txn.status_code == 400

    # confirm payment - success
    confirm = client.patch(f"/api/v1/payments/{payment['id']}/status?is_success=true", headers=auth_headers(attendee_token))
    assert confirm.status_code == 200
    assert confirm.json()["data"]["payment_status"] == "SUCCESS"

    # cannot confirm twice
    confirm_again = client.patch(f"/api/v1/payments/{payment['id']}/status?is_success=true", headers=auth_headers(attendee_token))
    assert confirm_again.status_code == 400

    # registration should now be CONFIRMED
    reg_check = client.get(f"/api/v1/registrations/{registration['id']}", headers=auth_headers(admin_token)).json()["data"]
    assert reg_check["registration_status"] == "CONFIRMED"

    # check-in
    checkin = client.post(f"/api/v1/registrations/{registration['id']}/check-in",
        json={"check_in_method": "MANUAL"}, headers=auth_headers(organizer_token))
    assert checkin.status_code == 200

    # duplicate check-in blocked
    checkin_again = client.post(f"/api/v1/registrations/{registration['id']}/check-in",
        json={"check_in_method": "MANUAL"}, headers=auth_headers(organizer_token))
    assert checkin_again.status_code == 400

    # certificate - only works because checked in
    cert = client.post(f"/api/v1/certificates/generate/{registration['id']}",
        json={"certificate_type": "PARTICIPATION"}, headers=auth_headers(organizer_token))
    assert cert.status_code == 201

    # feedback - only works because checked in
    feedback = client.post("/api/v1/feedback",
        json={"event_id": event["id"], "rating": 5, "feedback": "Great event!"}, headers=auth_headers(attendee_token))
    assert feedback.status_code == 201

    # duplicate feedback on same target blocked
    feedback_again = client.post("/api/v1/feedback",
        json={"event_id": event["id"], "rating": 3}, headers=auth_headers(attendee_token))
    assert feedback_again.status_code == 400


def test_payment_failure_releases_ticket_quantity(client, organizer_token, attendee_token):
    event = _create_event_open_now(client, organizer_token)
    registration = client.post(f"/api/v1/events/{event['id']}/register", headers=auth_headers(attendee_token)).json()["data"]

    now = datetime.now(timezone.utc)
    ticket = client.post(f"/api/v1/events/{event['id']}/tickets",
        json={"ticket_type": "VIP", "price": 5000.00, "quantity": 5,
              "sale_start": (now - timedelta(days=1)).isoformat(), "sale_end": (now + timedelta(days=3)).isoformat()},
        headers=auth_headers(organizer_token)).json()["data"]
    assert ticket["available_quantity"] == 5

    purchase = client.post(f"/api/v1/tickets/{ticket['id']}/purchase",
        json={"registration_id": registration["id"], "quantity": 2}, headers=auth_headers(attendee_token)).json()["data"]

    # available_quantity should have dropped to 3 immediately at purchase time
    tickets_list = client.get(f"/api/v1/events/{event['id']}/tickets", headers=auth_headers(attendee_token)).json()["data"]
    assert tickets_list[0]["available_quantity"] == 3

    payment = client.post(f"/api/v1/payments/{purchase['id']}",
        json={"payment_method": "CARD", "transaction_id": "TXNFAIL001"}, headers=auth_headers(attendee_token)).json()["data"]

    # mark payment as FAILED
    fail = client.patch(f"/api/v1/payments/{payment['id']}/status?is_success=false", headers=auth_headers(attendee_token))
    assert fail.status_code == 200
    assert fail.json()["data"]["payment_status"] == "FAILED"

    # available_quantity should be released back to 5
    tickets_list_after = client.get(f"/api/v1/events/{event['id']}/tickets", headers=auth_headers(attendee_token)).json()["data"]
    assert tickets_list_after[0]["available_quantity"] == 5


def test_session_booking_requires_confirmed_registration(client, organizer_token, attendee_token):
    event = _create_event_open_now(client, organizer_token)
    venue = client.post("/api/v1/venues",
        json={"venue_name": "V1", "address": "1 Main Street", "city": "Bengaluru", "capacity": 100},
        headers=auth_headers(organizer_token)).json()["data"]
    hall = client.post(f"/api/v1/venues/{venue['id']}/halls",
        json={"hall_name": "H1", "capacity": 50}, headers=auth_headers(organizer_token)).json()["data"]

    event_start = datetime.fromisoformat(event["start_date"])
    session = client.post("/api/v1/sessions",
        json={"event_id": event["id"], "hall_id": hall["id"], "title": "Talk", "start_time": (event_start + timedelta(hours=1)).isoformat(),
              "end_time": (event_start + timedelta(hours=2)).isoformat(), "capacity": 30},
        headers=auth_headers(organizer_token)).json()["data"]

    client.post(f"/api/v1/events/{event['id']}/register", headers=auth_headers(attendee_token))

    # registration is only PENDING (never paid), so booking should be blocked
    booking = client.post(f"/api/v1/sessions/{session['id']}/book", headers=auth_headers(attendee_token))
    assert booking.status_code == 400