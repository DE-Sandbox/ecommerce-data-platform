"""Audit-related SQLAlchemy models."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class AuditLog(Base):
    """Audit log model for tracking all database changes."""

    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("uuid_generate_v7()"),
        nullable=False,
    )
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    record_id: Mapped[UUID] = mapped_column(UUID(as_uuid=False), nullable=False)
    action: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # INSERT, UPDATE, DELETE
    user_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    old_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    changed_fields: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    audit_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default={},
        server_default=text("'{}'::jsonb"),
    )

    __table_args__ = ({"schema": "audit"},)
