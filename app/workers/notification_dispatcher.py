from app.database import SessionLocal
from app.queue import notification_queue
from app.models import Notification, NotificationStatus
import time

def dispatch_notifications():
    print("Notification dispatcher started")

    with SessionLocal() as db:
        notifications = (
            db.query(Notification)
            .filter(Notification.status == NotificationStatus.PENDING)
            .all()
        )

        for notification in notifications:
            try:
                notification.status = NotificationStatus.ENQUEUED

                notification_queue.put(notification.id)

                db.commit()

            except Exception as exc:
                db.rollback()
                print(
                    f"Failed to enqueue notification "
                    f"{notification.id}: {exc}"
                )

def run():
    print("Notification dispatcher started")

    while True:
        dispatch_notifications()
        time.sleep(2)


if __name__ == "__main__":
    run()