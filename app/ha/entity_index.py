"""Read-only entity indexing and target-resolution previews for Home Assistant."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Iterable

from app.llm.schema import IntentResult, IntentTarget

DEVICE_TYPE_DOMAINS = {
    "light": "light",
    "switch": "switch",
    "thermostat": "climate",
}


@dataclass(frozen=True)
class IndexedEntity:
    """A supported Home Assistant entity available for resolution preview."""

    entity_id: str
    domain: str
    friendly_name: str
    state: str


@dataclass(frozen=True)
class ResolutionPreview:
    """A non-executing view of entities that could satisfy an intent target."""

    resolved: bool
    reason: str
    matches: tuple[IndexedEntity, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the preview."""

        return {
            "resolved": self.resolved,
            "reason": self.reason,
            "matches": [asdict(entity) for entity in self.matches],
        }


class EntityIndex:
    """Index supported Home Assistant entity states for deterministic matching."""

    def __init__(self, entities: Iterable[IndexedEntity]) -> None:
        """Initialize an index from supported entity records."""

        self._entities = tuple(entities)
        self._by_id = {entity.entity_id: entity for entity in self._entities}

    @classmethod
    def from_states(cls, states: Iterable[dict[str, Any]]) -> "EntityIndex":
        """Build an index from Home Assistant's read-only state response."""

        entities: list[IndexedEntity] = []
        for state in states:
            entity_id = state.get("entity_id")
            if not isinstance(entity_id, str) or "." not in entity_id:
                continue
            domain = entity_id.split(".", maxsplit=1)[0]
            if domain not in DEVICE_TYPE_DOMAINS.values():
                continue

            attributes = state.get("attributes")
            friendly_name = (
                attributes.get("friendly_name")
                if isinstance(attributes, dict)
                else None
            )
            entities.append(
                IndexedEntity(
                    entity_id=entity_id,
                    domain=domain,
                    friendly_name=(
                        friendly_name if isinstance(friendly_name, str) else entity_id
                    ),
                    state=str(state.get("state", "unknown")),
                )
            )
        return cls(entities)

    def preview(self, intent: IntentResult) -> ResolutionPreview:
        """Preview matches for a validated intent without executing any action."""

        if intent.needs_clarification:
            return ResolutionPreview(
                resolved=False,
                reason="Intent requires clarification before target resolution.",
                matches=(),
            )
        return self.preview_target(intent.target)

    def preview_target(self, target: IntentTarget) -> ResolutionPreview:
        """Preview matches for one intent target without calling Home Assistant."""

        if target.entity_id:
            entity = self._by_id.get(target.entity_id)
            if entity is None:
                return ResolutionPreview(
                    resolved=False,
                    reason="The requested entity_id is not available in the supported index.",
                    matches=(),
                )
            if not _matches_device_type(entity, target.device_type):
                return ResolutionPreview(
                    resolved=False,
                    reason="The requested entity_id does not match the requested device type.",
                    matches=(),
                )
            return ResolutionPreview(
                resolved=True,
                reason="Matched the explicit entity_id.",
                matches=(entity,),
            )

        if not target.room:
            return ResolutionPreview(
                resolved=False,
                reason="A room or entity_id is required for target resolution.",
                matches=(),
            )

        matches = tuple(
            entity
            for entity in self._entities
            if _matches_device_type(entity, target.device_type)
            and _matches_room(entity, target.room)
        )
        if not matches:
            return ResolutionPreview(
                resolved=False,
                reason="No supported entities matched the requested room and device type.",
                matches=(),
            )
        return ResolutionPreview(
            resolved=True,
            reason="Matched entities by normalized room and device type.",
            matches=matches,
        )


def _matches_device_type(entity: IndexedEntity, device_type: str | None) -> bool:
    """Return whether an indexed entity matches the requested device type."""

    if device_type is None:
        return True
    return entity.domain == DEVICE_TYPE_DOMAINS[device_type]


def _matches_room(entity: IndexedEntity, room: str) -> bool:
    """Match every normalized room word against the entity ID or friendly name."""

    room_words = set(_normalize_words(room))
    entity_words = set(_normalize_words(f"{entity.entity_id} {entity.friendly_name}"))
    return bool(room_words) and room_words.issubset(entity_words)


def _normalize_words(value: str) -> tuple[str, ...]:
    """Convert identifiers and display names into lowercase matching words."""

    return tuple(word for word in re.split(r"[^a-z0-9]+", value.lower()) if word)
