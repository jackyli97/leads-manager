from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Lead, User
from app.schemas import LeadCreate, LeadRead, LeadStatusUpdate
from app.services.assignment_service import select_attorney_id
from app.services.notification_service import create_lead_notifications
from app.services.storage import delete_resume, save_resume

router = APIRouter(prefix="/leads", tags=["leads"])
DatabaseSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def parse_lead_form(
    first_name: Annotated[str, Form()],
    last_name: Annotated[str, Form()],
    email: Annotated[str, Form()],
) -> LeadCreate:
    try:
        return LeadCreate(first_name=first_name, last_name=last_name, email=email)
    except ValidationError as error:
        raise RequestValidationError(error.errors()) from error


@router.get("", response_model=list[LeadRead])
def list_leads(db: DatabaseSession, _: CurrentUser) -> list[Lead]:
    return list(db.scalars(select(Lead).order_by(Lead.id.desc())).all())


@router.patch("/{lead_id}/status", response_model=LeadRead)
def update_lead_status(
    lead_id: int,
    status_update: LeadStatusUpdate,
    db: DatabaseSession,
    _: CurrentUser,
) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    if lead.status != status_update.status:
        lead.status = status_update.status
        db.commit()
        db.refresh(lead)

    return lead


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: Annotated[LeadCreate, Depends(parse_lead_form)],
    resume: Annotated[UploadFile, File()],
    db: DatabaseSession,
) -> Lead:
    existing_lead_id = db.scalar(select(Lead.id).where(Lead.email == str(lead_data.email)))
    if existing_lead_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A lead with this email already exists",
        )

    resume_url = await save_resume(resume)
    assigned_attorney_id = select_attorney_id(db)
    assigned_attorney = (
        db.get(User, assigned_attorney_id) if assigned_attorney_id is not None else None
    )
    lead = Lead(
        first_name=lead_data.first_name,
        last_name=lead_data.last_name,
        email=str(lead_data.email),
        resume_url=resume_url,
        assigned_attorney_id=assigned_attorney_id,
    )
    db.add(lead)
    db.add_all(create_lead_notifications(lead, assigned_attorney))

    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        await delete_resume(resume_url)
        if isinstance(error, IntegrityError) and db.scalar(
            select(Lead.id).where(Lead.email == str(lead_data.email))
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A lead with this email already exists",
            ) from None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create lead notifications",
        ) from None

    db.refresh(lead)
    return lead
