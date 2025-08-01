"""Base event classes and interfaces for the event schema registry."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.events.taxonomy import EVENT_SOURCE, EVENT_VERSION


class EventMetadata(BaseModel):
    """Standard metadata for all events."""

    event_id: UUID = Field(description="Unique identifier for this event instance")
    event_type: str = Field(description="Type of event (e.g., 'order.created')")
    event_version: str = Field(default=EVENT_VERSION, description="Schema version")
    event_source: str = Field(
        default=EVENT_SOURCE, description="System that generated the event"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the event occurred",
    )
    correlation_id: UUID | None = Field(
        default=None,
        description="ID to correlate related events",
    )
    causation_id: UUID | None = Field(
        default=None,
        description="ID of the event that caused this event",
    )
    actor_id: str | None = Field(
        default=None,
        description="ID of the user or system that triggered the event",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "01234567-89ab-cdef-0123-456789abcdef",
                "event_type": "order.created",
                "event_version": "1.0",
                "event_source": "ecommerce-platform",
                "timestamp": "2025-01-01T12:00:00Z",
                "correlation_id": "fedcba98-7654-3210-fedc-ba9876543210",
                "actor_id": "user:12345",
            }
        }
    )


class BaseEvent[TEventData: BaseModel](BaseModel):
    """Base class for all domain events."""

    metadata: EventMetadata
    data: TEventData

    model_config = ConfigDict(
        json_schema_extra={
            "description": "Base structure for all domain events",
            "required": ["metadata", "data"],
        }
    )

    def to_message(self) -> dict[str, str | dict[str, str]]:
        """Convert event to message format for streaming."""
        return {
            "headers": {
                "event_id": str(self.metadata.event_id),
                "event_type": self.metadata.event_type,
                "event_version": self.metadata.event_version,
                "timestamp": self.metadata.timestamp.isoformat(),
            },
            "key": str(self.metadata.event_id),
            "value": self.model_dump_json(),
        }


class EventRegistry(ABC):
    """Abstract base class for event schema registry."""

    @abstractmethod
    def register_schema(
        self,
        event_type: str,
        schema: type[BaseModel],
        version: str = EVENT_VERSION,
    ) -> None:
        """Register an event schema.

        Args:
            event_type: The event type (e.g., 'order.created')
            schema: The Pydantic model for the event data
            version: The schema version

        """

    @abstractmethod
    def get_schema(
        self,
        event_type: str,
        version: str | None = None,
    ) -> type[BaseModel] | None:
        """Get the schema for an event type.

        Args:
            event_type: The event type
            version: The schema version (latest if None)

        Returns:
            The schema class or None if not found

        """

    @abstractmethod
    def validate_event(self, event: dict[str, object]) -> BaseEvent[BaseModel]:
        """Validate an event against its schema.

        Args:
            event: The event data as a dictionary

        Returns:
            The validated event object

        Raises:
            ValidationError: If the event is invalid

        """

    @abstractmethod
    def get_schema_evolution_path(
        self,
        event_type: str,
        from_version: str,
        to_version: str,
    ) -> list[str]:
        """Get the migration path between schema versions.

        Args:
            event_type: The event type
            from_version: The starting version
            to_version: The target version

        Returns:
            List of versions in the migration path

        """

    def list_event_types(self) -> list[str]:
        """List all registered event types."""
        raise NotImplementedError

    def list_versions(self, event_type: str) -> list[str]:
        """List all versions for an event type."""
        raise NotImplementedError


class SchemaVersion(BaseModel):
    """Schema version metadata."""

    version: str = Field(description="Version identifier (e.g., '1.0', '1.1')")
    schema_class: type[BaseModel] = Field(description="The Pydantic schema class")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this version was registered",
    )
    deprecated: bool = Field(
        default=False,
        description="Whether this version is deprecated",
    )
    compatible_with: list[str] = Field(
        default_factory=list,
        description="List of versions this is backward compatible with",
    )
    migration_notes: str | None = Field(
        default=None,
        description="Notes about migrating from previous versions",
    )
