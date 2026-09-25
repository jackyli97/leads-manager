import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Lead, Notification, NotificationType


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)


@pytest.mark.parametrize("notification_type", list(NotificationType))
def test_notification_type_must_be_unique_per_lead(
    db_session: Session,
    notification_type: NotificationType,
):
    lead = Lead(
        first_name="Grace",
        last_name="Hopper",
        email="grace@example.com",
        resume_url="/uploads/grace-hopper.pdf",
    )
    lead.notifications.extend(
        [
            Notification(
                type=notification_type,
                recipient_email=lead.email,
            ),
            Notification(
                type=notification_type,
                recipient_email=lead.email,
            ),
        ]
    )
    db_session.add(lead)

    with pytest.raises(IntegrityError):
        db_session.commit()
