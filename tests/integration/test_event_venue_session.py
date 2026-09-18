from tests.conftest import auth_headers

def _create_event(client, organizer_token, start_offset_days=30):
    from datetime import datetime, timedelta, timezone
    start = (datetime.now(timezone.utc) + timedelta(days=start_offset_days)).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=start_offset_days + 1)).isoformat()
    reg_start = datetime.now(timezone.utc).isoformat()
    reg_end = (datetime.now(timezone.utc) + timedelta(days=start_offset_days - 1)).isoformat()
    response = client.post("/api/v1/events",
        json={"event_name": "TechConf", "event_type": "CONFERENCE", "start_date": start, "end_date": end,
              "registration_start": reg_start, "registration_end": reg_end, "capacity": 100},
        headers=auth_headers(organizer_token))
    return response.json()["data"]


def test_event_date_validation(client, organizer_token):
    from datetime import datetime, timedelta, timezone
    start = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    bad_end = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()  # before start
    response = client.post("/api/v1/events",
        json={"event_name": "Bad Event", "event_type": "CONFERENCE", "start_date": start, "end_date": bad_end,
              "registration_start": datetime.now(timezone.utc).isoformat(), "registration_end": start, "capacity": 50},
        headers=auth_headers(organizer_token))
    assert response.status_code == 422


def test_create_event_success(client, organizer_token):
    event = _create_event(client, organizer_token)
    assert event["status"] == "DRAFT"


def test_venue_and_hall_capacity_check(client, organizer_token):
    venue = client.post("/api/v1/venues",
        json={"venue_name": "Grand Center", "address": "1 Main St", "city": "Bengaluru", "capacity": 100},
        headers=auth_headers(organizer_token)).json()["data"]

    over_capacity = client.post(f"/api/v1/venues/{venue['id']}/halls",
        json={"hall_name": "Hall A", "capacity": 200}, headers=auth_headers(organizer_token))
    assert over_capacity.status_code == 400

    valid_hall = client.post(f"/api/v1/venues/{venue['id']}/halls",
        json={"hall_name": "Hall A", "capacity": 80}, headers=auth_headers(organizer_token))
    assert valid_hall.status_code == 201


def test_session_hall_overlap_blocked(client, organizer_token):
    event = _create_event(client, organizer_token)
    venue = client.post("/api/v1/venues",
        json={"venue_name": "Venue X", "address": "1 Main Street", "city": "Bengaluru", "capacity": 200},
        headers=auth_headers(organizer_token)).json()["data"]
    hall = client.post(f"/api/v1/venues/{venue['id']}/halls",
        json={"hall_name": "Main Hall", "capacity": 100}, headers=auth_headers(organizer_token)).json()["data"]

    from datetime import datetime, timedelta, timezone
    event_start = datetime.fromisoformat(event["start_date"])
    s1_start = (event_start + timedelta(hours=1)).isoformat()
    s1_end = (event_start + timedelta(hours=2)).isoformat()

    first_session = client.post("/api/v1/sessions",
        json={"event_id": event["id"], "hall_id": hall["id"], "title": "Session 1", "start_time": s1_start, "end_time": s1_end, "capacity": 50},
        headers=auth_headers(organizer_token))
    assert first_session.status_code == 201

    # overlapping time, same hall
    overlap_session = client.post("/api/v1/sessions",
        json={"event_id": event["id"], "hall_id": hall["id"], "title": "Session 2", "start_time": s1_start, "end_time": s1_end, "capacity": 50},
        headers=auth_headers(organizer_token))
    assert overlap_session.status_code == 400