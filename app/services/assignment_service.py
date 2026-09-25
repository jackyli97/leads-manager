from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Lead, User, UserRole


def select_attorney_id(db: Session) -> int | None:
    statement = (
        select(User.id)
        .outerjoin(Lead, Lead.assigned_attorney_id == User.id)
        .where(User.role == UserRole.ATTORNEY)
        .group_by(User.id)
        .order_by(func.count(Lead.id), User.id)
        .limit(1)
    )
    return db.scalar(statement)
