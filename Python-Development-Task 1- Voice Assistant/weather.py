"""Weather command handler."""


from voice_assistant.commands.base import BaseCommand, CommandContext, CommandResult
from voice_assistant.config.constants import IntentType
from voice_assistant.errors.exceptions import WeatherServiceError
from voice_assistant.nlp.intent import IntentResult
from voice_assistant.observability.logging import get_logger
from voice_assistant.services.weather.provider import WeatherService

logger = get_logger(__name__)


class WeatherCommand(BaseCommand):
    """Fetches live weather reports using configured WeatherService."""

    def __init__(self, weather_service: WeatherService):
        self.weather_service = weather_service

    @property
    def name(self) -> str:
        return "WeatherCommand"

    @property
    def description(self) -> str:
        return "Fetches current weather conditions and temperature for a given location."

    @property
    def supported_intents(self) -> set[IntentType]:
        return {IntentType.WEATHER}

    def execute(self, intent_result: IntentResult, context: CommandContext) -> CommandResult:
        location = intent_result.entities.get("location")

        if not location:
            # Check if location can be obtained from context or ask user
            return CommandResult.fail("Which city or location would you like the weather for?")

        try:
            weather_data = self.weather_service.get_weather(location)
            speech_text = weather_data.to_speech_text()
            return CommandResult.ok(
                speech_text,
                data={
                    "location": weather_data.location,
                    "temperature": weather_data.temperature_celsius,
                    "description": weather_data.description,
                    "humidity": weather_data.humidity,
                },
            )
        except WeatherServiceError as e:
            logger.warning(f"Weather query failed for '{location}': {e}")
            return CommandResult.fail(f"I couldn't get the weather for {location}: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error during weather retrieval: {e}")
            return CommandResult.fail("Sorry, I encountered an issue retrieving the weather right now.")
