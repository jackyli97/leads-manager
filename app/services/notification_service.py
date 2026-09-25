from app.models import Lead, Notification, NotificationType, User


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
