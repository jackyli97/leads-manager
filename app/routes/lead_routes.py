from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead
from app.schemas import LeadCreate, LeadRead
from app.services.assignment_service import select_attorney_id
from app.services.storage import delete_resume, save_resume

router = APIRouter(prefix="/leads", tags=["leads"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def parse_lead_form(
    first_name: Annotated[str, Form()],
    last_name: Annotated[str, Form()],
    email: Annotated[str, Form()],
) -> LeadCreate:
    try:
        return LeadCreate(first_name=first_name, last_name=last_name, email=email)
    except ValidationError as error:
        raise RequestValidationError(error.errors()) from error


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: Annotated[LeadCreate, Depends(parse_lead_form)],
    resume: Annotated[UploadFile, File()],
    db: DatabaseSession,
) -> Lead:
    resume_url = await save_resume(resume)
    lead = Lead(
        first_name=lead_data.first_name,
        last_name=lead_data.last_name,
        email=str(lead_data.email),
        resume_url=resume_url,
        assigned_attorney_id=select_attorney_id(db),
    )
    db.add(lead)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        await delete_resume(resume_url)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A lead with this email already exists",
        ) from None

    db.refresh(lead)
    return lead
