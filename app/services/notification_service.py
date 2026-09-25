from app.models import Lead, Notification, NotificationType, User, NotificationStatus
from sqlalchemy.orm import Session
from app.services.email_service import send_email

def create_lead_notifications(
    lead: Lead,
    assigned_attorney: User | None,
) -> list[Notification]:
    return [
        Notification(
            lead=lead,
            type=NotificationType.LEAD_CONFIRMATION,
            recipient_email=lead.email,
        ),
        Notification(
            lead=lead,
            type=NotificationType.NOTIFY_ATTORNEY,
            recipient_email=assigned_attorney.email if assigned_attorney else None,
        ),
    ]


def process_notification(
    db: Session,
    notification_id: int,
):
    notification = db.get(Notification, notification_id)

    if notification is None:
        return

    if notification.status == NotificationStatus.SENT:
        return

    if not notification.recipient_email:
        print(
            f"Failed to process notification, missing recipient email "
            f"{notification.id}"
        )
        return

    try:
        send_email(
            to=notification.recipient_email,
            type=notification.type
        )

        notification.status = NotificationStatus.SENT

        db.commit()
    except Exception as exc:
        db.rollback()
        print(
            f"Failed to process notification "
            f"{notification.id}: {exc}"
        )
        raise