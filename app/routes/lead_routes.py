from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead
from app.schemas import LeadCreate, LeadRead
from app.services.assignment_service import select_attorney_id

router = APIRouter(prefix="/leads", tags=["leads"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(lead_data: LeadCreate, db: DatabaseSession) -> Lead:
    lead = Lead(
        first_name=lead_data.first_name,
        last_name=lead_data.last_name,
        email=str(lead_data.email),
        resume_url=lead_data.resume_url,
        assigned_attorney_id=select_attorney_id(db),
    )
    db.add(lead)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A lead with this email already exists",
        ) from None

    db.refresh(lead)
    return lead
