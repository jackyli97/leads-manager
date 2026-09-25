import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Lead, User
from app.services.assignment_service import select_attorney_id


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)


def create_attorney(db_session: Session, email: str) -> User:
    attorney = User(
        first_name="Test",
        last_name="Attorney",
        email=email,
        password="hashed-password",
    )
    db_session.add(attorney)
    db_session.flush()
    return attorney


def create_lead(db_session: Session, email: str, attorney_id: int) -> Lead:
    lead = Lead(
        first_name="Test",
        last_name="Lead",
        email=email,
        resume_url=f"/uploads/{email}.pdf",
        assigned_attorney_id=attorney_id,
    )
    db_session.add(lead)
    db_session.flush()
    return lead


def test_select_attorney_returns_none_when_no_attorneys_exist(db_session: Session):
    assert select_attorney_id(db_session) is None


def test_select_attorney_prefers_attorney_with_no_leads(db_session: Session):
    busy_attorney = create_attorney(db_session, "busy@example.com")
    available_attorney = create_attorney(db_session, "available@example.com")
    create_lead(db_session, "lead@example.com", busy_attorney.id)

    assert select_attorney_id(db_session) == available_attorney.id


def test_select_attorney_returns_attorney_with_fewest_leads(db_session: Session):
    busy_attorney = create_attorney(db_session, "busy@example.com")
    less_busy_attorney = create_attorney(db_session, "less-busy@example.com")
    create_lead(db_session, "lead-1@example.com", busy_attorney.id)
    create_lead(db_session, "lead-2@example.com", busy_attorney.id)
    create_lead(db_session, "lead-3@example.com", less_busy_attorney.id)

    assert select_attorney_id(db_session) == less_busy_attorney.id


def test_select_attorney_allows_any_attorney_when_counts_are_tied(db_session: Session):
    first_attorney = create_attorney(db_session, "first@example.com")
    second_attorney = create_attorney(db_session, "second@example.com")

    assert select_attorney_id(db_session) in {first_attorney.id, second_attorney.id}
