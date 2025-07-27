"""Base model configuration for SQLAlchemy."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.schema import MetaData

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    metadata = metadata


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
    )


class VersionMixin:
    """Mixin for optimistic locking."""

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """Base model with common fields."""

    __abstract__ = True

    # Use UUID type with PostgreSQL's UUID_GENERATE_V7() function
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),  # Store as UUID type, not Python uuid
        primary_key=True,
        server_default=text("UUID_GENERATE_V7()"),
        nullable=False,
    )

    def __repr__(self) -> str:
        """Return string representation of the model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class BaseModelNoSoftDelete(Base, TimestampMixin):
    """Base model without soft delete fields."""

    __abstract__ = True

    # Use UUID type with PostgreSQL's UUID_GENERATE_V7() function
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),  # Store as UUID type, not Python uuid
        primary_key=True,
        server_default=text("UUID_GENERATE_V7()"),
        nullable=False,
    )

    def __repr__(self) -> str:
        """Return string representation of the model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"
