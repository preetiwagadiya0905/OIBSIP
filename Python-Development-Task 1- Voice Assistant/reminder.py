"""Reminder command handler for asynchronous scheduling and cancellation."""


from voice_assistant.commands.base import BaseCommand, CommandContext, CommandResult
from voice_assistant.config.constants import IntentType
from voice_assistant.errors.exceptions import ReminderError
from voice_assistant.nlp.intent import IntentResult
from voice_assistant.observability.logging import get_logger
from voice_assistant.services.reminders.scheduler import ReminderScheduler

logger = get_logger(__name__)


class ReminderCommand(BaseCommand):
    """Schedules background timed reminders with audible chime and spoken notification."""

    def __init__(self, scheduler: ReminderScheduler):
        self.scheduler = scheduler

    @property
    def name(self) -> str:
        return "ReminderCommand"

    @property
    def description(self) -> str:
        return "Schedules, lists, and cancels timed background reminders."

    @property
    def supported_intents(self) -> set[IntentType]:
        return {IntentType.SET_REMINDER}

    def execute(self, intent_result: IntentResult, context: CommandContext) -> CommandResult:
        entities = intent_result.entities
        duration_seconds = entities.get("duration_seconds")
        message = entities.get("message", "Reminder alert")

        if duration_seconds is None:
            return CommandResult.fail(
                "When would you like to be reminded? For example, say 'remind me in 10 minutes to call John'."
            )

        try:
            reminder = self.scheduler.schedule(
                duration_seconds=duration_seconds,
                message=message,
            )
            response = f"Sure. I will remind you in {reminder.human_duration} to {reminder.message}."
            return CommandResult.ok(
                response,
                data={
                    "reminder_id": reminder.id,
                    "duration_seconds": reminder.duration_seconds,
                    "message": reminder.message,
                },
            )
        except ReminderError as e:
            return CommandResult.fail(f"Could not set reminder: {e.message}")
        except Exception as e:
            logger.error(f"Failed to schedule reminder: {e}")
            return CommandResult.fail("Sorry, I could not schedule that reminder.")
