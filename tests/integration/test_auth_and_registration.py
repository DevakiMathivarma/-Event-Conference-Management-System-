from tests.conftest import auth_headers

def test_admin_login(client, admin_token):
    assert admin_token is not None

def test_register_requires_admin(client):
    response = client.post("/api/v1/auth/register",
        json={"full_name": "Sneaky", "email": "sneaky@test.com", "phone": "9555555555", "password": "Test@1234", "role": "EVENT_ORGANIZER"})
    assert response.status_code == 401

def test_attendee_self_registers_no_token_needed(client):
    response = client.post("/api/v1/attendees",
        json={"full_name": "Self Reg", "email": "selfreg@test.com", "phone": "9888888888", "password": "Test@1234"})
    assert response.status_code == 201

def test_activation_blocks_self_change(client, admin_token):
    me = client.get("/api/v1/auth/me", headers=auth_headers(admin_token)).json()["data"]
    response = client.put(f"/api/v1/auth/{me['id']}/activation", json={"is_active": False}, headers=auth_headers(admin_token))
    assert response.status_code == 400