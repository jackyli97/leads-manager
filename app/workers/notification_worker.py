from app.database import SessionLocal
from app.queue import notification_queue
from app.services.notification_service import process_notification


def run_worker():
    print("Notification worker started")

    while True:
        notification_id = notification_queue.get()

        db = SessionLocal()

        try:
            process_notification(db=db, notification_id=int(notification_id))
            notification_queue.task_done()

        except Exception as exc:
            print(
                f"Failed to process notification "
                f"{notification_id}: {exc}"
            )

            notification_queue.task_done()
            notification_queue.put(notification_id)

        finally:
            db.close()


if __name__ == "__main__":
    run_worker()