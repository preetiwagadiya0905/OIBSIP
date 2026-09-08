"""Custom user-defined commands executor and registrar."""

import webbrowser

from voice_assistant.commands.base import BaseCommand, CommandContext, CommandResult
from voice_assistant.config.constants import CustomActionType, IntentType
from voice_assistant.errors.exceptions import SecurityValidationError
from voice_assistant.nlp.intent import IntentResult
from voice_assistant.observability.logging import get_logger
from voice_assistant.storage.custom_commands import CustomCommandsStorage

logger = get_logger(__name__)


class CustomCommandsCommand(BaseCommand):
    """Executes existing user-defined commands and handles creation of new custom commands."""

    def __init__(self, storage: CustomCommandsStorage):
        self.storage = storage

    @property
    def name(self) -> str:
        return "CustomCommandsCommand"

    @property
    def description(self) -> str:
        return "Executes custom user actions and allows registration of new custom voice commands."

    @property
    def supported_intents(self) -> set[IntentType]:
        return {IntentType.ADD_COMMAND}

    def execute(self, intent_result: IntentResult, context: CommandContext) -> CommandResult:
        entities = intent_result.entities
        name = entities.get("name")
        action_str = entities.get("action")
        target = entities.get("target")

        if not name or not action_str or not target:
            return CommandResult.fail(
                "To add a custom command, say: 'create a command called [name] that opens [URL]' "
                "or 'create a command called [name] that speaks [text]'."
            )

        try:
            action = CustomActionType(action_str)
            created = self.storage.add_command(
                name=name,
                action=action,
                target=target,
                description=f"User custom {action.value} command",
            )
            return CommandResult.ok(
                f"Custom command '{created.name}' has been created successfully. "
                f"You can now trigger it anytime.",
                data={"command": created.name, "action": created.action.value, "target": created.target},
            )
        except (ValueError, SecurityValidationError) as e:
            return CommandResult.fail(f"Could not create custom command: {e}")
        except Exception as e:
            logger.error(f"Failed to create custom command: {e}")
            return CommandResult.fail("An error occurred while saving the custom command.")

    def try_execute_custom(self, normalized_query: str) -> CommandResult:
        """Check if query matches a registered custom command and execute it."""
        cmd = self.storage.get_command(normalized_query)
        if not cmd:
            return CommandResult.fail(f"No custom command found matching '{normalized_query}'.")

        logger.info(f"Executing custom command '{cmd.name}' (action={cmd.action.value})")

        if cmd.action == CustomActionType.OPEN_URL:
            try:
                webbrowser.open_new_tab(cmd.target)
                return CommandResult.ok(f"Opening {cmd.name}.", data={"url": cmd.target})
            except Exception as e:
                logger.error(f"Failed to open custom URL {cmd.target}: {e}")
                return CommandResult.fail(f"Could not open URL: {e}")

        elif cmd.action == CustomActionType.SPEAK:
            return CommandResult.ok(cmd.target, data={"speak_text": cmd.target})

        return CommandResult.fail(f"Unsupported action '{cmd.action.value}'.")
