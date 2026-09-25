# leads-manager

## Functional Requirements
- Form in UI for prospective customers to fill out information
- Form data is persisted
- After lead is submitted, emails will be sent:
	- To prospect
	- To internal attorney
- Internal auth guarded UI to render list of all leads and their filled out info
- Every lead has a state
	- pending -> initial
	- reached out
		- to transition to this state, internal attorney needs to manually mark
- Support files for resume/csv
## Non Functional Requirements
- At least once delivery for post lead emails to prospect and attorney - aim for de-duplication
- Minimize latency after form submission(~1s) -> Email sending should not block form success
- Uphold invariance for valid state transitions
	- Only support pending to reached out
- Handle validations of emails and avoid storing / saving to duplicate emails

## Core Entities
- User
- Lead
- Notification

## Data Modeling
- Users Table
	- first name
	- last name
	- role(enum)
		- attorney(only available type for now)
	- email(unique)
	- password
- Lead
	- first name
	- last name
	- email (unique)
	- resume / csv (url)
	- assigned_attorney (reference to users table)
	- status (enum)
		- pending(initial)
		- reached_out
- Notification
	- type
		- lead_confirmation(sent to lead)
		- notify_attorney(sent to attorney)
	- recipient_email
	- status
		- pending(initial - before enqueued)
		- enqueued(added to queue)
		- sent
		- failed

## Required technologies
- SQLite for database
- Resend for email service

## Notes
- Using SQLite for local development and ease of setup, but in production environment would default to a client-server DB like Postgres
- Storing PDFs on disk for minimal setup, in production environment, would use S3
- In production environment would use a persistent queue solution like SQS, but for time constraint purposes, using asyncio.Queue here. This mimics enqueue, worker execute, clean up flow, but will not gracefully handle queue crashes