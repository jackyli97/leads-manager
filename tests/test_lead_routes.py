import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Lead, LeadStatus, User
from app.services import storage

PDF_CONTENT = b"%PDF-1.4\n% test resume\n%%EOF"


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


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)
    return tmp_path


def lead_payload(email: str = "grace@example.com"):
    return {
        "first_name": "Grace",
        "last_name": "Hopper",
        "email": email,
    }


def submit_lead(client: TestClient, email: str = "grace@example.com"):
    return client.post(
        "/leads",
        data=lead_payload(email),
        files={"resume": ("resume.pdf", PDF_CONTENT, "application/pdf")},
    )


def test_create_lead(client: TestClient, db_session: Session, upload_dir):
    response = submit_lead(client, "GRACE@example.com")

    assert response.status_code == 201
    response_data = response.json()
    resume_url = response_data.pop("resume_url")
    assert response_data == {
        "id": 1,
        "first_name": "Grace",
        "last_name": "Hopper",
        "email": "grace@example.com",
        "assigned_attorney_id": None,
        "status": LeadStatus.PENDING.value,
    }
    assert resume_url.startswith("/uploads/")
    assert (upload_dir / resume_url.removeprefix("/uploads/")).read_bytes() == PDF_CONTENT

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

    response = submit_lead(client)

    assert response.status_code == 201
    assert response.json()["assigned_attorney_id"] == attorney.id


def test_create_lead_rejects_duplicate_email(client: TestClient, upload_dir):
    assert submit_lead(client).status_code == 201

    response = submit_lead(client, "GRACE@example.com")

    assert response.status_code == 409
    assert response.json() == {"detail": "A lead with this email already exists"}
    assert len(list(upload_dir.glob("*.pdf"))) == 1


def test_create_lead_requires_resume_file(client: TestClient):
    response = client.post("/leads", data=lead_payload())

    assert response.status_code == 422


def test_create_lead_rejects_non_pdf(client: TestClient, upload_dir):
    response = client.post(
        "/leads",
        data=lead_payload(),
        files={"resume": ("resume.txt", b"not a PDF", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Resume must be a valid PDF file"}
    assert list(upload_dir.iterdir()) == []
