import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Lead, LeadStatus, User


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        yield session

    Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def lead_payload(email: str = "grace@example.com"):
    return {
        "first_name": "Grace",
        "last_name": "Hopper",
        "email": email,
        "resume_url": "/uploads/grace-hopper.pdf",
    }


def test_create_lead(client: TestClient, db_session: Session):
    response = client.post("/leads", json=lead_payload("GRACE@example.com"))

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "first_name": "Grace",
        "last_name": "Hopper",
        "email": "grace@example.com",
        "resume_url": "/uploads/grace-hopper.pdf",
        "assigned_attorney_id": None,
        "status": LeadStatus.PENDING.value,
    }

    lead = db_session.scalar(select(Lead))
    assert lead is not None
    assert lead.assigned_attorney_id is None


def test_create_lead_assigns_available_attorney(
    client: TestClient, db_session: Session
):
    attorney = User(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        password="hashed-password",
    )
    db_session.add(attorney)
    db_session.commit()

    response = client.post("/leads", json=lead_payload())

    assert response.status_code == 201
    assert response.json()["assigned_attorney_id"] == attorney.id


def test_create_lead_rejects_duplicate_email(client: TestClient):
    assert client.post("/leads", json=lead_payload()).status_code == 201

    response = client.post("/leads", json=lead_payload("GRACE@example.com"))

    assert response.status_code == 409
    assert response.json() == {"detail": "A lead with this email already exists"}


def test_create_lead_requires_resume_url(client: TestClient):
    payload = lead_payload()
    payload.pop("resume_url")

    response = client.post("/leads", json=payload)

    assert response.status_code == 422
