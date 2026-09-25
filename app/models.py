from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(StrEnum):
    ATTORNEY = "attorney"


class LeadStatus(StrEnum):
    PENDING = "pending"
    REACHED_OUT = "reached_out"


class NotificationType(StrEnum):
    LEAD_CONFIRMATION = "lead_confirmation"
    NOTIFY_ATTORNEY = "notify_attorney"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    ENQUEUED = "enqueued"
    SENT = "sent"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda roles: [role.value for role in roles]),
        nullable=False,
        default=UserRole.ATTORNEY,
        server_default=UserRole.ATTORNEY.value,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_leads: Mapped[list["Lead"]] = relationship(back_populates="assigned_attorney")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    resume_url: Mapped[str] = mapped_column(String(500), nullable=False)
    assigned_attorney_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    status: Mapped[LeadStatus] = mapped_column(
        Enum(
            LeadStatus,
            name="lead_status",
            values_callable=lambda statuses: [status.value for status in statuses],
        ),
        nullable=False,
        default=LeadStatus.PENDING,
        server_default=LeadStatus.PENDING.value,
    )

    assigned_attorney: Mapped[User | None] = relationship(back_populates="assigned_leads")
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
    )


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("lead_id", "type", name="uq_notifications_lead_id_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    type: Mapped[NotificationType] = mapped_column(
        Enum(
            NotificationType,
            name="notification_type",
            values_callable=lambda types: [notification_type.value for notification_type in types],
        ),
        nullable=False,
    )
    recipient_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(
            NotificationStatus,
            name="notification_status",
            values_callable=lambda statuses: [status.value for status in statuses],
        ),
        nullable=False,
        default=NotificationStatus.PENDING,
        server_default=NotificationStatus.PENDING.value,
    )

    lead: Mapped[Lead] = relationship(back_populates="notifications")
