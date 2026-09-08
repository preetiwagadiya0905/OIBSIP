"""Audio-specific errors re-exported for convenience."""

from voice_assistant.errors.exceptions import (
    AudioError,
    MicrophoneError,
    SpeechRecognitionError,
    SpeechTimeoutError,
    TextToSpeechError,
    UnknownSpeechError,
)

__all__ = [
    "AudioError",
    "MicrophoneError",
    "SpeechRecognitionError",
    "SpeechTimeoutError",
    "UnknownSpeechError",
    "TextToSpeechError",
]
