"""Command base interface, context, and result models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from voice_assistant.config.constants import IntentType
from voice_assistant.nlp.intent import IntentResult


@dataclass(frozen=True)
class CommandResult:
    """Outcome of command execution."""
    response_text: str
    success: bool = True
    should_exit: bool = False
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, response_text: str, data: dict[str, Any] | None = None, should_exit: bool = False) -> "CommandResult":
        return cls(response_text=response_text, success=True, should_exit=should_exit, data=data or {})

    @classmethod
    def fail(cls, error_text: str, data: dict[str, Any] | None = None) -> "CommandResult":
        return cls(response_text=error_text, success=False, should_exit=False, data=data or {})


@dataclass
class CommandContext:
    """Runtime context and dependencies passed into command handlers."""
    services: dict[str, Any] = field(default_factory=dict)
    app_state: Any = None

    def get(self, service_name: str) -> Any:
        """Retrieve a registered application service."""
        return self.services.get(service_name)


class BaseCommand(ABC):
    """Abstract Base Class for all voice assistant commands."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable command name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief summary of what this command accomplishes."""
        ...

    @property
    @abstractmethod
    def supported_intents(self) -> set[IntentType]:
        """Set of IntentTypes this command can execute."""
        ...

    @abstractmethod
    def execute(self, intent_result: IntentResult, context: CommandContext) -> CommandResult:
        """Execute the command and return a CommandResult with speech response."""
        ...
