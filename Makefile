dev:
	.venv/bin/uvicorn app.main:app --reload

web:
	npm --prefix frontend run dev

dispatcher:
	.venv/bin/python -m app.workers.notification_dispatcher

worker:
	.venv/bin/python -m app.workers.notification_worker
