"""Domain models for intent classification and parsing results."""

from dataclasses import dataclass, field
from typing import Any

from voice_assistant.config.constants import IntentType


@dataclass(frozen=True)
class IntentResult:
    """Represents the parsed intent, confidence score, and extracted entities."""
    intent: IntentType
    confidence: float
    raw_text: str
    normalized_text: str
    entities: dict[str, Any] = field(default_factory=dict)
    requires_clarification: bool = False
    clarification_prompt: str | None = None

    @property
    def is_confident(self) -> bool:
        """Whether the classification exceeds confidence standards and requires no clarification."""
        return not self.requires_clarification and self.confidence >= 0.50

    @classmethod
    def unknown(cls, raw_text: str, normalized_text: str) -> "IntentResult":
        """Factory for unrecognized utterances."""
        return cls(
            intent=IntentType.UNKNOWN,
            confidence=0.0,
            raw_text=raw_text,
            normalized_text=normalized_text,
            entities={},
            requires_clarification=False,
        )

    @classmethod
    def clarify(
        cls,
        intent: IntentType,
        confidence: float,
        raw_text: str,
        normalized_text: str,
        prompt: str,
        entities: dict[str, Any] | None = None,
    ) -> "IntentResult":
        """Factory for low-confidence or ambiguous classifications requiring clarification."""
        return cls(
            intent=intent,
            confidence=confidence,
            raw_text=raw_text,
            normalized_text=normalized_text,
            entities=entities or {},
            requires_clarification=True,
            clarification_prompt=prompt,
        )
