"""Greeting and conversational introduction command."""

import datetime

from voice_assistant.commands.base import BaseCommand, CommandContext, CommandResult
from voice_assistant.config.constants import IntentType
from voice_assistant.nlp.intent import IntentResult


class GreetingCommand(BaseCommand):
    """Responds to greetings with time-aware and friendly responses."""

    @property
    def name(self) -> str:
        return "GreetingCommand"

    @property
    def description(self) -> str:
        return "Responds with a friendly, time-appropriate greeting."

    @property
    def supported_intents(self) -> set[IntentType]:
        return {IntentType.GREETING}

    def execute(self, intent_result: IntentResult, context: CommandContext) -> CommandResult:
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            period = "Good morning!"
        elif 12 <= hour < 17:
            period = "Good afternoon!"
        elif 17 <= hour < 22:
            period = "Good evening!"
        else:
            period = "Hello!"

        response = f"{period} I am Aura, your voice assistant. How can I help you today?"
        return CommandResult.ok(response)
