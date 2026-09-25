from persistqueue import FIFOSQLiteQueue

notification_queue = FIFOSQLiteQueue(
    path="./data/notification_queue",
    multithreading=True,
)
