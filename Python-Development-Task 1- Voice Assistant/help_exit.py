"""Help, Exit, and Cancellation command handlers."""


from voice_assistant.application.session import SessionManager
from voice_assistant.commands.base import BaseCommand, CommandContext, CommandResult
from voice_assistant.config.constants import IntentType
from voice_assistant.nlp.intent import IntentResult


class HelpCommand(BaseCommand):
    """Provides conversational help and feature summary."""

    @property
    def name(self) -> str:
        return "HelpCommand"

    @property
    def description(self) -> str:
        return "Explains assistant features and supported voice capabilities."

    @property
    def supported_intents(self) -> set[IntentType]:
        return {IntentType.HELP}

    def execute(self, intent_result: IntentResult, context: CommandContext) -> CommandResult:
        help_text = (
            "I can help you with several tasks. You can ask me to: "
            "tell you the current time or date, "
            "search the web for any topic, "
            "check live weather for any city, "
            "send an email via voice, "
            "set timed reminders with audible alerts, "
            "answer knowledge questions, "
            "or manage your custom commands."
        )
        return CommandResult.ok(help_text)


class ExitCommand(BaseCommand):
    """Gracefully terminates the assistant session."""

    @property
    def name(self) -> str:
        return "ExitCommand"

    @property
    def description(self) -> str:
        return "Shuts down the voice assistant."

    @property
    def supported_intents(self) -> set[IntentType]:
        return {IntentType.EXIT}

    def execute(self, intent_result: IntentResult, context: CommandContext) -> CommandResult:
        return CommandResult.ok("Goodbye! Have a wonderful day.", should_exit=True)


class CancelCommand(BaseCommand):
    """Cancels active workflow or session."""

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    @property
    def name(self) -> str:
        return "CancelCommand"

    @property
    def description(self) -> str:
        return "Cancels current conversational workflow."

    @property
    def supported_intents(self) -> set[IntentType]:
        return {IntentType.CANCEL}

    def execute(self, intent_result: IntentResult, context: CommandContext) -> CommandResult:
        if self.session_manager.has_active_session:
            self.session_manager.clear()
            return CommandResult.ok("Operation cancelled.")
        return CommandResult.ok("Nothing is currently in progress to cancel.")
