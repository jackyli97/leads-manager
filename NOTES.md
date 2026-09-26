# Coding Agent Usage and Attribution

## Short writeup

I used the OpenAI Codex coding agent in the shared repository workspace. It inspected the existing FastAPI, SQLAlchemy, Pydantic, SQLite, and Next.js code; edited files with patches; and used shell commands to inspect the project, install declared packages, inspect SQLite schemas, and run pytest, ESLint, and Next.js builds. No work was delegated to a subagent. The agent wrote implementation and focused tests in response to my prompts because the work was scoped to this codebase and could be checked locally. I supplied the product requirements and decisions, including the attorney-only role, lead status behavior, PDF intake, notification types, atomic creation, and least-loaded attorney assignment. I installed/configured Resend and supplied its API key through local environment configuration; secrets are not included here.

One subtly incorrect implementation appeared when the lead endpoint combined a Pydantic model parameter using `Form()` with a separate `UploadFile`. The code looked reasonable, but FastAPI returned `422` because it expected the entire model under one `lead_data` form field. Endpoint tests exposed the mismatch. The model was changed to a dependency that receives individual form fields, constructs the Pydantic model explicitly, and preserves its validation. The multipart endpoint tests then passed.

## Representative prompt excerpts

Excerpts from the development conversation:

> “Firstly create the users table”

> “now create a leads table”

> “assigned_attorney_id should also be nullable”

> “create the boilerplate to support create leads endpoint, i will add the custom logic for supporting assigned_attorney_id myself”

> “for select_attorney_id, can we query the users table for the attorney type, and sort by the number of assigned_leads”

> “update the resume field, to be a file uploader”

> “support the creation of a notification table, and make sure the there is a unique constraint of each type and the lead_id”

> “allow attorney to update the status in the ui”

The implementation was refined through follow-up prompts and local test feedback, including changing lead statuses to be reversible and adding notification uniqueness coverage.

## Attribution

No commits were created for this work. This file records attribution at the project level:

- Agent-generated from user-directed prompts: the initial user and lead models/schemas, authentication and lead API scaffolding, attorney assignment service, PDF upload path, notification model and atomic lead-notification creation, and the related tests and Next.js authentication, intake, and attorney portal UI.
- User-implemented: the notification queue, worker, and dispatcher.
- User-provided direction and decisions: the feature requirements and schema choices expressed in the conversation, local Resend installation and API key configuration, and subsequent review and corrections requested in the IDE.
- User-owned material: `.env` and its secret values, README edits already present in the worktree, and any direct edits not explicitly described above. This attribution does not claim that every current line in a shared file was written by one party.

The agent did not inspect or reproduce secret values in this document.
