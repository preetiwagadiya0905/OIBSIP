"""Domain and infrastructure exception hierarchy for Voice Assistant."""



class VoiceAssistantError(Exception):
    """Base exception for all Voice Assistant errors."""

    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


# Configuration & Security Errors
class ConfigurationError(VoiceAssistantError):
    """Raised when configuration values are missing, malformed, or invalid."""


class SecurityValidationError(VoiceAssistantError):
    """Raised when an action, URL, or input violates security policy."""


# Audio Errors
class AudioError(VoiceAssistantError):
    """Base exception for audio subsystem errors."""


class MicrophoneError(AudioError):
    """Raised when microphone initialization, device query, or stream fails."""


class SpeechRecognitionError(AudioError):
    """Raised when speech recognition backend fails or encounters an unrecoverable error."""


class SpeechTimeoutError(SpeechRecognitionError):
    """Raised when listening times out before speech starts."""


class UnknownSpeechError(SpeechRecognitionError):
    """Raised when speech is detected but cannot be transcribed."""


class TextToSpeechError(AudioError):
    """Raised when speech synthesis fails."""


# NLU & Intent Errors
class NLUError(VoiceAssistantError):
    """Base exception for natural language understanding errors."""


class IntentClassificationError(NLUError):
    """Raised when intent classification encounters a fatal processing error."""


class EntityExtractionError(NLUError):
    """Raised when required entity extraction fails or yields invalid types."""


# Command & Workflow Errors
class CommandError(VoiceAssistantError):
    """Base exception for command execution failures."""


class CommandNotFoundError(CommandError):
    """Raised when no registered command can handle the requested intent."""


class ClarificationRequiredError(CommandError):
    """Raised when intent confidence is low or required parameters are ambiguous."""


class WorkflowCancelledError(CommandError):
    """Raised when a multi-turn conversation or task is cancelled by the user."""


# External Service Errors
class ExternalServiceError(VoiceAssistantError):
    """Base exception for third-party API / service errors."""


class WeatherServiceError(ExternalServiceError):
    """Raised when weather API, geocoding, or parsing fails."""


class EmailServiceError(ExternalServiceError):
    """Raised when SMTP connection, authentication, or dispatch fails."""


class KnowledgeServiceError(ExternalServiceError):
    """Raised when QA / knowledge base queries fail."""


class ReminderError(VoiceAssistantError):
    """Raised when scheduling, cancelling, or executing a reminder fails."""


class StorageError(VoiceAssistantError):
    """Raised when reading or persisting custom commands or local data fails."""
