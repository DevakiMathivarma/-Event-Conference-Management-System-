import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_celery_tasks(monkeypatch):
    # every service does a LOCAL import inside its function body
    # (from app.tasks import send_x_email), so the mock has to target
    # app.tasks itself, where the real task objects live
    class FakeDelay:
        def delay(self, *args, **kwargs):
            return None
    fake_task = FakeDelay()
    task_names = [
        "send_registration_confirmation_email", "send_payment_success_email", "send_ticket_confirmation_email",
        "send_certificate_availability_email", "send_event_cancellation_email", "send_refund_email",
        "send_event_reminder_email", "send_session_reminder_email"
    ]
    for task_name in task_names:
        monkeypatch.setattr(f"app.tasks.{task_name}", fake_task, raising=False)


@pytest.fixture(autouse=True)
def mock_pdf_and_qr(monkeypatch):
    monkeypatch.setattr("app.services.payment_service.generate_ticket_pdf", lambda **kwargs: "fake_ticket.pdf", raising=False)
    monkeypatch.setattr("app.services.payment_service.generate_registration_qr_code", lambda *args, **kwargs: "fake_qr.png", raising=False)
    monkeypatch.setattr("app.services.certificate_service.generate_certificate_pdf", lambda **kwargs: "fake_certificate.pdf", raising=False)


@pytest.fixture(autouse=True)
def mock_websocket_broadcast(monkeypatch):
    monkeypatch.setattr("app.services.check_in_service.broadcast_check_in_update_sync", lambda *args, **kwargs: None, raising=False)


@pytest.fixture(autouse=True)
def disable_rate_limiting(monkeypatch):
    monkeypatch.setattr("app.utils.rate_limit.redis_client.get", lambda key: None)


@pytest.fixture
def admin_token(client, db_session) -> str:
    from app.models.user import User, UserRole
    from app.utils.hashing import hash_password

    admin = db_session.query(User).filter(User.role == UserRole.ADMIN).first()
    if not admin:
        admin = User(full_name="Test Admin", email="admin@example.com", phone="9000000000",
            password_hash=hash_password("Admin@12345"), role=UserRole.ADMIN, is_active=True)
        db_session.add(admin)
        db_session.commit()

    response = client.post("/api/v1/auth/login", data={"username": "admin@example.com", "password": "Admin@12345"})
    return response.json()["access_token"]


@pytest.fixture
def organizer_token(client, admin_token) -> str:
    client.post("/api/v1/auth/register",
        json={"full_name": "Test Organizer", "email": "organizer@test.com", "phone": "9111111111", "password": "Test@1234", "role": "EVENT_ORGANIZER"},
        headers={"Authorization": f"Bearer {admin_token}"})
    response = client.post("/api/v1/auth/login", data={"username": "organizer@test.com", "password": "Test@1234"})
    return response.json()["access_token"]


@pytest.fixture
def attendee_token(client):
    client.post("/api/v1/attendees", json={"full_name": "Test Attendee", "email": "attendee@test.com", "phone": "9222222222", "password": "Test@1234"})
    response = client.post("/api/v1/auth/login", data={"username": "attendee@test.com", "password": "Test@1234"})
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}