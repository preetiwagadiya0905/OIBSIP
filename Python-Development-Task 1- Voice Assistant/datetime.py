"""Date and time query commands."""

import datetime

from voice_assistant.commands.base import BaseCommand, CommandContext, CommandResult
from voice_assistant.config.constants import IntentType
from voice_assistant.nlp.intent import IntentResult


class DateTimeCommand(BaseCommand):
    """Answers queries regarding current local time and calendar date."""

    @property
    def name(self) -> str:
        return "DateTimeCommand"

    @property
    def description(self) -> str:
        return "Provides the current local time and date."

    @property
    def supported_intents(self) -> set[IntentType]:
        return {IntentType.TIME, IntentType.DATE}

    def execute(self, intent_result: IntentResult, context: CommandContext) -> CommandResult:
        now = datetime.datetime.now()

        if intent_result.intent == IntentType.TIME:
            time_str = now.strftime("%I:%M %p").lstrip("0")
            return CommandResult.ok(f"The current time is {time_str}.")

        if intent_result.intent == IntentType.DATE:
            # Format: Sunday, August 16, 2026
            date_str = now.strftime("%A, %B %d, %Y")
            return CommandResult.ok(f"Today is {date_str}.")

        return CommandResult.fail("Could not determine requested date/time format.")
