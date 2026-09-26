# Local Development

## Requirements

- Python 3.12 or later
- Node.js 20.9 or later and npm
- A Resend API key to run the email worker

## Setup

From the repository root, create the Python environment and install dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
npm --prefix frontend ci
```

Create a root `.env` file for the notification worker:

```dotenv
RESEND_API_KEY=re_...
AUTH_SECRET_KEY=replace-with-a-long-random-value
```

Before starting a process in each terminal, export the `.env` values:

```sh
set -a
source .env
set +a
```

The API uses `AUTH_SECRET_KEY` to sign login tokens; use a long random value. Without it, the application falls back to a development-only key. The email worker uses `RESEND_API_KEY`. Do not commit `.env` or real credentials.

## Run

Start each process in its own terminal from the repository root:

```sh
set -a && source .env && set +a
make dev
```

```sh
set -a && source .env && set +a
make web
```

Open <http://localhost:3000>. The API is at <http://localhost:8000>, with interactive documentation at <http://localhost:8000/docs>.

To process email notifications, start both background processes in additional terminals:

```sh
set -a && source .env && set +a
make dispatcher
```

```sh
set -a && source .env && set +a
make worker
```

The dispatcher moves pending notification rows to the persistent SQLite queue; the worker sends them through Resend. The current email service directs messages to Resend's test recipient (`delivered@resend.dev`) while developing.

## Local Data

- SQLite database: `leads_manager.db` in the repository root. Tables are created on API startup.
- Uploaded PDF resumes: `uploads/` in the repository root, served under `/uploads/`.
- Persistent notification queue: `data/notification_queue/`.

These local data paths are ignored by Git. Keep copies you need; they are local development data, not source-controlled fixtures.
