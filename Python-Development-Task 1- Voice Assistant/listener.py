"""Audio listening and speech recognition abstractions."""

from typing import Protocol

import speech_recognition as sr

from voice_assistant.config.settings import AudioSettings
from voice_assistant.errors.exceptions import (
    MicrophoneError,
    SpeechRecognitionError,
    SpeechTimeoutError,
    UnknownSpeechError,
)
from voice_assistant.observability.logging import get_logger
from voice_assistant.security.validators import sanitize_speech_input

logger = get_logger(__name__)


class AudioListener(Protocol):
    """Protocol for capturing user spoken audio and converting to text."""

    def listen(self, prompt: str | None = None) -> str:
        """Listen for user audio and return the transcribed text."""
        ...

    def calibrate_noise(self, duration: float = 1.0) -> None:
        """Calibrate microphone for ambient noise levels."""
        ...

    def list_microphones(self) -> list[str]:
        """Return list of available microphone device names."""
        ...


class SpeechRecognitionListener:
    """Production microphone listener using SpeechRecognition library."""

    def __init__(self, settings: AudioSettings):
        self.settings = settings
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self._microphone: sr.Microphone | None = None
        self._initialize_microphone()

    def _initialize_microphone(self) -> None:
        """Initialize the microphone device safely."""
        try:
            mic_index = self.settings.microphone_index
            self._microphone = sr.Microphone(device_index=mic_index)
            logger.info(
                f"Initialized microphone with device_index={mic_index or 'default'}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize microphone device: {e}")
            self._microphone = None
            raise MicrophoneError("Failed to initialize microphone device", details=str(e)) from e

    def calibrate_noise(self, duration: float = 1.0) -> None:
        """Calibrate energy threshold based on ambient background noise."""
        if not self._microphone:
            raise MicrophoneError("Microphone is not available for noise calibration.")
        try:
            logger.info(f"Calibrating microphone for ambient noise ({duration}s)...")
            with self._microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            logger.info(
                f"Noise calibration complete. Energy threshold set to {self.recognizer.energy_threshold:.1f}"
            )
        except Exception as e:
            logger.warning(f"Noise calibration encountered an issue: {e}")

    def list_microphones(self) -> list[str]:
        """Return names of available microphone devices."""
        try:
            return sr.Microphone.list_microphone_names()
        except Exception as e:
            logger.error(f"Failed to query microphone device list: {e}")
            return []

    def listen(self, prompt: str | None = None) -> str:
        """Listen from the microphone and transcribe spoken audio using Google Speech Recognition API."""
        if not self._microphone:
            raise MicrophoneError("Microphone is not initialized or unavailable.")

        if prompt:
            logger.debug(f"Listening prompt: {prompt}")

        try:
            with self._microphone as source:
                logger.debug("Listening for voice input...")
                audio = self.recognizer.listen(
                    source,
                    timeout=self.settings.speech_timeout,
                    phrase_time_limit=self.settings.phrase_time_limit,
                )

            logger.debug("Audio captured, transcribing speech...")
            transcription = self.recognizer.recognize_google(audio, language="en-US")
            sanitized = sanitize_speech_input(transcription)
            logger.info(f"Recognized speech: '{sanitized}'")
            return sanitized

        except sr.WaitTimeoutError as e:
            logger.debug("Listening timed out with no speech detected.")
            raise SpeechTimeoutError("No speech detected within timeout period.") from e

        except sr.UnknownValueError as e:
            logger.debug("Speech detected but could not be understood.")
            raise UnknownSpeechError("Could not understand audio.") from e

        except sr.RequestError as e:
            logger.error(f"Speech recognition service request error: {e}")
            raise SpeechRecognitionError(
                "Speech recognition service unavailable", details=str(e)
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error during audio listening: {e}")
            raise SpeechRecognitionError("Audio capture failure", details=str(e)) from e


class ConsoleAudioListener:
    """CLI/Text-based listener for text mode, demonstrations, and headless environments."""

    def __init__(self) -> None:
        logger.info("Initialized ConsoleAudioListener for text input mode.")

    def calibrate_noise(self, duration: float = 1.0) -> None:
        """No-op for text listener."""
        logger.debug("Console audio listener noise calibration (no-op).")

    def list_microphones(self) -> list[str]:
        return ["Console Standard Input"]

    def listen(self, prompt: str | None = None) -> str:
        """Prompt user on the terminal and read standard input line."""
        prompt_text = "\n[User (Type command)]> " if not prompt else f"\n[{prompt}] > "
        try:
            user_input = input(prompt_text).strip()
            if not user_input:
                raise SpeechTimeoutError("Empty input received.")
            sanitized = sanitize_speech_input(user_input)
            logger.info(f"Received console input: '{sanitized}'")
            return sanitized
        except (KeyboardInterrupt, EOFError) as e:
            logger.info("Console input cancelled.")
            raise SpeechTimeoutError("User terminated input.") from e


class MockAudioListener:
    """Mock listener for automated unit and integration tests."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self.responses = list(responses or [])
        self.call_count = 0

    def add_response(self, text: str) -> None:
        self.responses.append(text)

    def calibrate_noise(self, duration: float = 1.0) -> None:
        pass

    def list_microphones(self) -> list[str]:
        return ["Mock Virtual Microphone"]

    def listen(self, prompt: str | None = None) -> str:
        self.call_count += 1
        if not self.responses:
            raise SpeechTimeoutError("Mock listener has no remaining queued responses.")
        next_response = self.responses.pop(0)
        if isinstance(next_response, Exception):
            raise next_response
        return sanitize_speech_input(next_response)
