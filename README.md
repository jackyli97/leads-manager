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
    - lead_id (reference to leads table)
    - unique constraint on type and lead_id

## Design Choice for email delivery delegated to queue
- Goal: To ensure emails are delivered at least once, and they don't block form submission. Relegate email delivery to background so they don't block processes and can be processed concurrently
- Adding a Notifications object. Every email that should be sent(2 per lead, 1 to lead and 1 to attorney) should have a corresponding Notifications object created, with a status of pending.
- A dispatcher works in the background querying for notifications that have a status of pending, and adds to our queue.
- Queue is built on top of sqlite3 so it is durable and support appends, reappends, and removal following completion
- Another worker runs in the background that picks tasks from the queue and executes the task(sending email). On failures, we re-append notifiation to the queue. A future improvement can be to record number of overall failures and per notificaiton failure - and halt execution of worker if it seems like email provider is down, or to stop appending notification to queue after x amount of failures

## Required technologies
- SQLite for database
- Resend for email service
- Persist queue library(https://github.com/peter-wangxu/persist-queue) for durable queue built on top of sql lite

## Notes
- Using SQLite for local development and ease of setup, but in production environment would default to a client-server DB like Postgres
- Storing PDFs on disk for minimal setup, in production environment, would use S3
- In production environment would use a persistent queue solution like SQS, but for time constraint purposes, using asyncio.Queue here. This mimics enqueue, worker execute, clean up flow, but will not gracefully handle queue crashes