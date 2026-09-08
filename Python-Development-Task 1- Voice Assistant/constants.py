"""Application constants, enumerations, and default limits."""

from enum import Enum


class AppState(str, Enum):
    """Lifecycle and runtime state of the Voice Assistant."""
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    CONFIRMING = "CONFIRMING"
    EXECUTING = "EXECUTING"
    SHUTTING_DOWN = "SHUTTING_DOWN"


class AppEnvironment(str, Enum):
    """Runtime environment."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class IntentType(str, Enum):
    """Supported user intents."""
    GREETING = "GREETING"
    TIME = "TIME"
    DATE = "DATE"
    WEB_SEARCH = "WEB_SEARCH"
    WEATHER = "WEATHER"
    SEND_EMAIL = "SEND_EMAIL"
    SET_REMINDER = "SET_REMINDER"
    KNOWLEDGE = "KNOWLEDGE"
    ADD_COMMAND = "ADD_COMMAND"
    HELP = "HELP"
    EXIT = "EXIT"
    CONFIRMATION_YES = "CONFIRMATION_YES"
    CONFIRMATION_NO = "CONFIRMATION_NO"
    CANCEL = "CANCEL"
    UNKNOWN = "UNKNOWN"


class CustomActionType(str, Enum):
    """Allowlisted actions for user-defined custom commands."""
    OPEN_URL = "open_url"
    SPEAK = "speak"


class ReminderStatus(str, Enum):
    """Status of scheduled reminders."""
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# Defaults & Constraints
DEFAULT_SPEECH_TIMEOUT: float = 5.0
DEFAULT_PHRASE_TIME_LIMIT: float = 10.0
DEFAULT_HTTP_TIMEOUT: float = 8.0
DEFAULT_SMTP_TIMEOUT: float = 10.0
DEFAULT_NLP_THRESHOLD: float = 0.50
DEFAULT_TTS_RATE: int = 175
DEFAULT_TTS_VOLUME: float = 1.0
DEFAULT_WEATHER_UNITS: str = "metric"
DEFAULT_WEATHER_LANGUAGE: str = "en"
DEFAULT_COMMANDS_FILE: str = "config/commands.json"

MAX_REMINDER_DURATION_SECONDS: int = 86400 * 30  # 30 days
MIN_REMINDER_DURATION_SECONDS: int = 1

CONFIRMATION_YES_WORDS = {
    "yes", "yeah", "yep", "sure", "confirm", "send it", "do it",
    "proceed", "affirmative", "correct", "absolutely", "ok", "okay"
}

CONFIRMATION_NO_WORDS = {
    "no", "nope", "cancel", "stop", "never mind", "forget it",
    "abort", "don't", "dont", "do not"
}

CANCELLATION_WORDS = {
    "cancel", "cancel that", "never mind", "forget it", "abort", "stop this", "stop"
}
