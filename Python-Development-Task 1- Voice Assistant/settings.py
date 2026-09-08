"""Centralized, typed application configuration management."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from voice_assistant.config.constants import (
    DEFAULT_COMMANDS_FILE,
    DEFAULT_HTTP_TIMEOUT,
    DEFAULT_NLP_THRESHOLD,
    DEFAULT_PHRASE_TIME_LIMIT,
    DEFAULT_SMTP_TIMEOUT,
    DEFAULT_SPEECH_TIMEOUT,
    DEFAULT_TTS_RATE,
    DEFAULT_TTS_VOLUME,
    DEFAULT_WEATHER_LANGUAGE,
    DEFAULT_WEATHER_UNITS,
    AppEnvironment,
)
from voice_assistant.errors.exceptions import ConfigurationError


@dataclass(frozen=True)
class AudioSettings:
    """Audio input/output settings."""
    tts_rate: int = DEFAULT_TTS_RATE
    tts_volume: float = DEFAULT_TTS_VOLUME
    tts_voice_index: int = 0
    microphone_index: int | None = None
    speech_timeout: float = DEFAULT_SPEECH_TIMEOUT
    phrase_time_limit: float = DEFAULT_PHRASE_TIME_LIMIT


@dataclass(frozen=True)
class WeatherSettings:
    """OpenWeatherMap service settings."""
    api_key: str = ""
    units: str = DEFAULT_WEATHER_UNITS
    language: str = DEFAULT_WEATHER_LANGUAGE
    http_timeout: float = DEFAULT_HTTP_TIMEOUT

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())


@dataclass(frozen=True)
class SMTPSettings:
    """SMTP client settings."""
    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    email_from: str = ""
    use_tls: bool = True
    timeout: float = DEFAULT_SMTP_TIMEOUT

    @property
    def is_configured(self) -> bool:
        return bool(self.host and self.username and self.password)


@dataclass(frozen=True)
class NLPSettings:
    """Natural Language Understanding settings."""
    confidence_threshold: float = DEFAULT_NLP_THRESHOLD


@dataclass(frozen=True)
class StorageSettings:
    """File storage & path settings."""
    commands_path: Path = field(default_factory=lambda: Path(DEFAULT_COMMANDS_FILE))


@dataclass(frozen=True)
class WebSettings:
    """FastAPI Web Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    rate_limit_per_minute: int = 60
    enable_public_email: bool = False


@dataclass(frozen=True)
class Settings:
    """Complete application settings bundle."""
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    app_name: str = "Aura Voice Assistant"
    log_level: str = "INFO"
    audio: AudioSettings = field(default_factory=AudioSettings)
    weather: WeatherSettings = field(default_factory=WeatherSettings)
    smtp: SMTPSettings = field(default_factory=SMTPSettings)
    nlp: NLPSettings = field(default_factory=NLPSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    web: WebSettings = field(default_factory=WebSettings)

    @classmethod
    def load(cls, env_file: str | None = None) -> "Settings":
        """Load settings from environment and optional .env file with validation."""
        if env_file:
            load_dotenv(dotenv_path=env_file, override=False)
        else:
            load_dotenv(override=False)

        # Environment
        raw_env = os.getenv("APP_ENV", "development").lower()
        try:
            app_env = AppEnvironment(raw_env)
        except ValueError:
            app_env = AppEnvironment.DEVELOPMENT

        app_name = os.getenv("APP_NAME", "Aura Voice Assistant")
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        # Audio
        try:
            tts_rate = int(os.getenv("TTS_RATE", str(DEFAULT_TTS_RATE)))
            tts_volume = float(os.getenv("TTS_VOLUME", str(DEFAULT_TTS_VOLUME)))
            tts_voice_index = int(os.getenv("TTS_VOICE_INDEX", "0"))
            mic_idx_str = os.getenv("MICROPHONE_INDEX")
            microphone_index = int(mic_idx_str) if mic_idx_str and mic_idx_str.strip() else None
            speech_timeout = float(os.getenv("SPEECH_TIMEOUT", str(DEFAULT_SPEECH_TIMEOUT)))
            phrase_time_limit = float(os.getenv("PHRASE_TIME_LIMIT", str(DEFAULT_PHRASE_TIME_LIMIT)))
        except ValueError as e:
            raise ConfigurationError(f"Invalid audio configuration values: {e}") from e

        # Validate bounds
        if not (50 <= tts_rate <= 400):
            raise ConfigurationError("TTS_RATE must be between 50 and 400 words per minute.")
        if not (0.0 <= tts_volume <= 1.0):
            raise ConfigurationError("TTS_VOLUME must be between 0.0 and 1.0.")

        audio_settings = AudioSettings(
            tts_rate=tts_rate,
            tts_volume=tts_volume,
            tts_voice_index=tts_voice_index,
            microphone_index=microphone_index,
            speech_timeout=speech_timeout,
            phrase_time_limit=phrase_time_limit,
        )

        # Weather
        http_timeout = float(os.getenv("HTTP_TIMEOUT", str(DEFAULT_HTTP_TIMEOUT)))
        weather_settings = WeatherSettings(
            api_key=os.getenv("OPENWEATHER_API_KEY", "").strip(),
            units=os.getenv("WEATHER_UNITS", DEFAULT_WEATHER_UNITS).strip(),
            language=os.getenv("WEATHER_LANGUAGE", DEFAULT_WEATHER_LANGUAGE).strip(),
            http_timeout=http_timeout,
        )

        # SMTP
        try:
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
            smtp_timeout = float(os.getenv("SMTP_TIMEOUT", str(DEFAULT_SMTP_TIMEOUT)))
        except ValueError as e:
            raise ConfigurationError(f"Invalid SMTP configuration: {e}") from e

        smtp_settings = SMTPSettings(
            host=os.getenv("SMTP_HOST", "").strip(),
            port=smtp_port,
            username=os.getenv("SMTP_USERNAME", "").strip(),
            password=os.getenv("SMTP_PASSWORD", "").strip(),
            email_from=os.getenv("EMAIL_FROM", "").strip() or os.getenv("SMTP_USERNAME", "").strip(),
            use_tls=smtp_use_tls,
            timeout=smtp_timeout,
        )

        # NLP
        try:
            nlp_threshold = float(os.getenv("NLP_CONFIDENCE_THRESHOLD", str(DEFAULT_NLP_THRESHOLD)))
        except ValueError as e:
            raise ConfigurationError(f"Invalid NLP_CONFIDENCE_THRESHOLD: {e}") from e
        if not (0.0 <= nlp_threshold <= 1.0):
            raise ConfigurationError("NLP_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0.")

        nlp_settings = NLPSettings(confidence_threshold=nlp_threshold)

        # Storage
        commands_path_str = os.getenv("CUSTOM_COMMANDS_PATH", DEFAULT_COMMANDS_FILE)
        storage_settings = StorageSettings(commands_path=Path(commands_path_str))

        # Web Server
        web_host = os.getenv("HOST", os.getenv("WEB_HOST", "0.0.0.0")).strip()
        try:
            web_port = int(os.getenv("PORT", os.getenv("WEB_PORT", "8000")))
            rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        except ValueError as e:
            raise ConfigurationError(f"Invalid Web configuration values: {e}") from e

        cors_str = os.getenv("CORS_ORIGINS", "*")
        cors_origins = [o.strip() for o in cors_str.split(",") if o.strip()]
        enable_public_email = os.getenv("ENABLE_PUBLIC_EMAIL", "false").lower() in ("1", "true", "yes")

        web_settings = WebSettings(
            host=web_host,
            port=web_port,
            cors_origins=cors_origins,
            rate_limit_per_minute=rate_limit,
            enable_public_email=enable_public_email,
        )

        return cls(
            app_env=app_env,
            app_name=app_name,
            log_level=log_level,
            audio=audio_settings,
            weather=weather_settings,
            smtp=smtp_settings,
            nlp=nlp_settings,
            storage=storage_settings,
            web=web_settings,
        )
