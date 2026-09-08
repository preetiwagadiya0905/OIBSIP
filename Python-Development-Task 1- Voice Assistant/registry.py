"""Command Registry for registering, discovering, and dispatching commands."""


from voice_assistant.commands.base import BaseCommand
from voice_assistant.config.constants import IntentType
from voice_assistant.errors.exceptions import CommandNotFoundError
from voice_assistant.observability.logging import get_logger

logger = get_logger(__name__)


class CommandRegistry:
    """Registry maintaining mappings of intent types to concrete command handlers."""

    def __init__(self) -> None:
        self._commands_by_intent: dict[IntentType, BaseCommand] = {}
        self._all_commands: list[BaseCommand] = []

    def register(self, command: BaseCommand) -> None:
        """Register a command handler for its supported intents."""
        if not isinstance(command, BaseCommand):
            raise TypeError("Command must inherit from BaseCommand")

        self._all_commands.append(command)
        for intent in command.supported_intents:
            if intent in self._commands_by_intent:
                logger.warning(
                    f"Overwriting handler for intent {intent.value}: "
                    f"{self._commands_by_intent[intent].name} -> {command.name}"
                )
            self._commands_by_intent[intent] = command
            logger.debug(f"Registered {command.name} for intent: {intent.value}")

    def get_command(self, intent: IntentType) -> BaseCommand:
        """Find command handler for a given intent."""
        if intent not in self._commands_by_intent:
            raise CommandNotFoundError(f"No command registered for intent '{intent.value}'.")
        return self._commands_by_intent[intent]

    def list_commands(self) -> list[BaseCommand]:
        """Return all uniquely registered commands."""
        return list(self._all_commands)
