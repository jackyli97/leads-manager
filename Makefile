dev:
	.venv/bin/uvicorn app.main:app --reload

web:
	npm --prefix frontend run dev
