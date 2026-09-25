import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Lead, LeadStatus, User


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)


def create_attorney(db_session: Session) -> User:
    attorney = User(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        password="hashed-password",
    )
    db_session.add(attorney)
    db_session.commit()
    return attorney


def test_lead_defaults_to_pending_and_references_attorney(db_session: Session):
    attorney = create_attorney(db_session)
    lead = Lead(
        first_name="Grace",
        last_name="Hopper",
        email="grace@example.com",
        resume_url="/uploads/grace-hopper.pdf",
        assigned_attorney_id=attorney.id,
    )

    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)

    assert lead.status is LeadStatus.PENDING
    assert lead.assigned_attorney == attorney
    assert attorney.assigned_leads == [lead]


def test_lead_can_be_created_without_assigned_attorney(db_session: Session):
    lead = Lead(
        first_name="Grace",
        last_name="Hopper",
        email="grace@example.com",
        resume_url="/uploads/grace-hopper.pdf",
    )

    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)

    assert lead.assigned_attorney_id is None
    assert lead.assigned_attorney is None


def test_lead_email_must_be_unique(db_session: Session):
    attorney = create_attorney(db_session)
    db_session.add_all(
        [
            Lead(
                first_name="Grace",
                last_name="Hopper",
                email="grace@example.com",
                resume_url="/uploads/grace-hopper.pdf",
                assigned_attorney_id=attorney.id,
            ),
            Lead(
                first_name="Another",
                last_name="Lead",
                email="grace@example.com",
                resume_url="/uploads/another-lead.pdf",
                assigned_attorney_id=attorney.id,
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_lead_requires_existing_attorney(db_session: Session):
    db_session.add(
        Lead(
            first_name="Grace",
            last_name="Hopper",
            email="grace@example.com",
            resume_url="/uploads/grace-hopper.pdf",
            assigned_attorney_id=999,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_lead_requires_resume_url(db_session: Session):
    attorney = create_attorney(db_session)
    db_session.add(
        Lead(
            first_name="Grace",
            last_name="Hopper",
            email="grace@example.com",
            assigned_attorney_id=attorney.id,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
