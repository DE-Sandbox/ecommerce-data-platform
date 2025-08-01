"""Event schema registry implementation."""

from collections import defaultdict
from typing import TypeVar

from pydantic import BaseModel

from src.events.base import BaseEvent, EventMetadata, EventRegistry, SchemaVersion
from src.events.taxonomy import validate_event_type

# Type variable for event data
TData = TypeVar("TData", bound=BaseModel)


class InMemoryEventRegistry(EventRegistry):
    """In-memory implementation of the event schema registry.

    This is suitable for single-instance applications. For distributed systems,
    consider using a shared registry like Confluent Schema Registry.
    """

    def __init__(self) -> None:
        """Initialize the registry.

        The registry maintains schemas in a nested dict structure:
        {event_type: {version: SchemaVersion}}
        """
        self._schemas: dict[str, dict[str, SchemaVersion]] = defaultdict(dict)
        self._latest_versions: dict[str, str] = {}

    def register_schema(
        self,
        event_type: str,
        schema: type[BaseModel],
        version: str = "1.0",
    ) -> None:
        """Register an event schema.

        Args:
            event_type: The event type (e.g., 'order.created')
            schema: The Pydantic model for the event data
            version: The schema version

        Raises:
            ValueError: If event type is invalid or schema already registered

        """
        if not validate_event_type(event_type):
            msg = f"Invalid event type: {event_type}"
            raise ValueError(msg)

        if event_type in self._schemas and version in self._schemas[event_type]:
            msg = f"Schema already registered for {event_type} version {version}"
            raise ValueError(msg)

        schema_version = SchemaVersion(version=version, schema_class=schema)
        self._schemas[event_type][version] = schema_version

        # Update latest version
        if (
            event_type not in self._latest_versions
            or self._compare_versions(version, self._latest_versions[event_type]) > 0
        ):
            self._latest_versions[event_type] = version

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
        if event_type not in self._schemas:
            return None

        if version is None:
            version = self._latest_versions.get(event_type)
            if version is None:
                return None

        schema_version = self._schemas[event_type].get(version)
        return schema_version.schema_class if schema_version else None

    def validate_event(self, event: dict[str, object]) -> BaseEvent[BaseModel]:
        """Validate an event against its schema.

        Args:
            event: The event data as a dictionary

        Returns:
            The validated event object

        Raises:
            ValidationError: If the event is invalid
            ValueError: If schema not found

        """
        metadata_raw = event.get("metadata")
        if not isinstance(metadata_raw, dict):
            msg = "Missing or invalid metadata"
            raise TypeError(msg)

        # Validate metadata
        metadata = EventMetadata(**metadata_raw)
        event_type = metadata.event_type
        event_version = metadata.event_version

        schema = self.get_schema(event_type, event_version)
        if not schema:
            msg = f"No schema found for {event_type} version {event_version}"
            raise ValueError(msg)

        # Validate the data portion
        data_raw = event.get("data")
        if not isinstance(data_raw, dict):
            msg = "Missing or invalid data"
            raise TypeError(msg)

        data = schema(**data_raw)

        # Create the full event with proper typing
        return BaseEvent(metadata=metadata, data=data)

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
        if event_type not in self._schemas:
            return []

        versions = sorted(
            self._schemas[event_type].keys(),
            key=lambda v: self._parse_version(v),
        )

        try:
            start_idx = versions.index(from_version)
            end_idx = versions.index(to_version)
        except ValueError:
            return []

        if start_idx > end_idx:
            return []

        return versions[start_idx : end_idx + 1]

    def list_event_types(self) -> list[str]:
        """List all registered event types."""
        return list(self._schemas.keys())

    def list_versions(self, event_type: str) -> list[str]:
        """List all versions for an event type."""
        if event_type not in self._schemas:
            return []
        return sorted(
            self._schemas[event_type].keys(),
            key=lambda v: self._parse_version(v),
        )

    def mark_deprecated(
        self,
        event_type: str,
        version: str,
        migration_notes: str | None = None,
    ) -> None:
        """Mark a schema version as deprecated.

        Args:
            event_type: The event type
            version: The version to deprecate
            migration_notes: Notes about migrating to newer versions

        """
        if event_type in self._schemas and version in self._schemas[event_type]:
            schema_version = self._schemas[event_type][version]
            schema_version.deprecated = True
            if migration_notes:
                schema_version.migration_notes = migration_notes

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare two version strings.

        Args:
            v1: First version
            v2: Second version

        Returns:
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2

        """
        parts1 = self._parse_version(v1)
        parts2 = self._parse_version(v2)

        for p1, p2 in zip(parts1, parts2, strict=False):
            if p1 < p2:
                return -1
            if p1 > p2:
                return 1

        return len(parts1) - len(parts2)

    def _parse_version(self, version: str) -> tuple[int, ...]:
        """Parse version string into tuple of integers."""
        return tuple(int(part) for part in version.split("."))


# Module-level registry state
class _RegistryState:
    """Container for registry singleton state."""

    registry: EventRegistry | None = None
    schemas_registered: bool = False


_state = _RegistryState()


def get_registry() -> EventRegistry:
    """Get the global event registry instance."""
    if _state.registry is None:
        _state.registry = InMemoryEventRegistry()
    return _state.registry


def set_registry(registry: EventRegistry) -> None:
    """Set the global event registry instance."""
    _state.registry = registry


def ensure_schemas_registered() -> None:
    """Ensure all schemas are registered exactly once."""
    if not _state.schemas_registered:
        # Lazy import to avoid circular dependencies
        from src.events.schemas import register_all_schemas

        register_all_schemas()
        _state.schemas_registered = True
