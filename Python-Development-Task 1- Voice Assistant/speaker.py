"""Text-to-speech speaker abstractions and pyttsx3 engine lifecycle."""

import threading
from typing import Protocol

import pyttsx3

from voice_assistant.config.settings import AudioSettings
from voice_assistant.errors.exceptions import TextToSpeechError
from voice_assistant.observability.logging import get_logger

logger = get_logger(__name__)


class AudioSpeaker(Protocol):
    """Protocol for speaking text responses."""

    def speak(self, text: str) -> None:
        """Speak the given text."""
        ...

    def stop(self) -> None:
        """Stop current speech output."""
        ...

    def shutdown(self) -> None:
        """Clean up audio resources."""
        ...


class Pyttsx3Speaker:
    """Thread-safe Text-to-Speech speaker using pyttsx3."""

    def __init__(self, settings: AudioSettings):
        self.settings = settings
        self._lock = threading.Lock()
        self._engine: pyttsx3.Engine | None = None
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize the pyttsx3 engine and configure voice attributes."""
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.settings.tts_rate)
            self._engine.setProperty("volume", self.settings.tts_volume)

            voices = self._engine.getProperty("voices")
            if voices and 0 <= self.settings.tts_voice_index < len(voices):
                selected_voice = voices[self.settings.tts_voice_index]
                self._engine.setProperty("voice", selected_voice.id)
                logger.info(f"Initialized TTS engine with voice: {selected_voice.name}")
            else:
                logger.info("Initialized TTS engine with default voice.")
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3 engine: {e}")
            self._engine = None
            raise TextToSpeechError("TTS Engine initialization failed", details=str(e)) from e

    def speak(self, text: str) -> None:
        """Speak the text synchronously under a thread lock to prevent audio race conditions."""
        if not text or not text.strip():
            return

        cleaned_text = text.strip()
        logger.info(f"Speaking: \"{cleaned_text}\"")

        with self._lock:
            if not self._engine:
                self._initialize_engine()

            try:
                if self._engine:
                    self._engine.say(cleaned_text)
                    self._engine.runAndWait()
            except Exception as e:
                import contextlib
                with contextlib.suppress(Exception):
                    self._initialize_engine()
                raise TextToSpeechError("Failed to speak text", details=str(e)) from e

    def stop(self) -> None:
        """Stop speech playback."""
        with self._lock:
            if self._engine:
                try:
                    self._engine.stop()
                except Exception as e:
                    logger.warning(f"Error stopping TTS engine: {e}")

    def shutdown(self) -> None:
        """Clean shutdown for speaker."""
        self.stop()
        self._engine = None
        logger.info("Pyttsx3Speaker shutdown complete.")


class ConsoleAudioSpeaker:
    """Text-only speaker for console/demo mode that prints formatted assistant responses."""

    def __init__(self, prefix: str = "[Aura Voice Assistant]"):
        self.prefix = prefix

    def speak(self, text: str) -> None:
        if not text:
            return
        cleaned = text.strip()
        logger.info(f"Speaking (Console): \"{cleaned}\"")
        print(f"\n{self.prefix}: {cleaned}")

    def stop(self) -> None:
        pass

    def shutdown(self) -> None:
        pass


class MockAudioSpeaker:
    """Mock speaker for testing that records all spoken utterances."""

    def __init__(self) -> None:
        self.spoken_phrases: list[str] = []

    def speak(self, text: str) -> None:
        if text:
            self.spoken_phrases.append(text.strip())

    def stop(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    @property
    def last_spoken(self) -> str | None:
        return self.spoken_phrases[-1] if self.spoken_phrases else None
