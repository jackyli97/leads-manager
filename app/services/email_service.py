import os
from dotenv import load_dotenv
import resend

# Load the .env file
load_dotenv()
resend.api_key = os.environ["RESEND_API_KEY"]
from app.models import NotificationType


FROM_EMAIL = "onboarding@resend.dev"

EMAIL_TEMPLATES: dict[NotificationType, dict[str, str]] = {
    NotificationType.LEAD_CONFIRMATION: {
        "subject": "We've received your information",
        "body": "Thank you for reaching out",
    },
    NotificationType.NOTIFY_ATTORNEY: {
        "subject": "New lead assigned to you",
        "body": "You have a new lead",
    },
}


def send_email(
    to: str,
    type: NotificationType
) -> str:
    subject = EMAIL_TEMPLATES[type]["subject"]
    body = EMAIL_TEMPLATES[type]["body"]
    
    params: resend.Emails.SendParams = {
        "from": FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": body,
    }

    email = resend.Emails.send(params)

    return email["id"]
