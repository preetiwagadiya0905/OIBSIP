"""Application builder and dependency injection factory."""


from voice_assistant.application.app import VoiceAssistantApp
from voice_assistant.application.lifecycle import LifecycleManager
from voice_assistant.application.session import SessionManager
from voice_assistant.audio.listener import (
    AudioListener,
    ConsoleAudioListener,
    SpeechRecognitionListener,
)
from voice_assistant.audio.speaker import (
    AudioSpeaker,
    ConsoleAudioSpeaker,
    Pyttsx3Speaker,
)
from voice_assistant.commands.custom import CustomCommandsCommand
from voice_assistant.commands.datetime import DateTimeCommand
from voice_assistant.commands.email import EmailCommand
from voice_assistant.commands.greeting import GreetingCommand
from voice_assistant.commands.help_exit import CancelCommand, ExitCommand, HelpCommand
from voice_assistant.commands.knowledge import KnowledgeCommand
from voice_assistant.commands.registry import CommandRegistry
from voice_assistant.commands.reminder import ReminderCommand
from voice_assistant.commands.weather import WeatherCommand
from voice_assistant.commands.web_search import WebSearchCommand
from voice_assistant.config.settings import Settings
from voice_assistant.nlp.classifier import HybridIntentClassifier
from voice_assistant.nlp.parser import NLUParser
from voice_assistant.observability.logging import get_logger
from voice_assistant.services.email.client import SMTPEmailClient
from voice_assistant.services.email.provider import EmailProvider, EmailService, SMTPEmailProvider
from voice_assistant.services.knowledge.client import (
    DuckDuckGoKnowledgeClient,
    WikipediaKnowledgeClient,
)
from voice_assistant.services.knowledge.provider import (
    CompositeKnowledgeProvider,
    KnowledgeProvider,
    KnowledgeService,
    LocalCuratedKnowledgeProvider,
)
from voice_assistant.services.reminders.scheduler import ReminderScheduler
from voice_assistant.services.weather.client import OpenWeatherMapClient
from voice_assistant.services.weather.geocoder import OpenWeatherMapGeocoder
from voice_assistant.services.weather.provider import (
    MockWeatherProvider,
    OpenWeatherMapProvider,
    WeatherProvider,
    WeatherService,
)
from voice_assistant.storage.custom_commands import CustomCommandsStorage

logger = get_logger(__name__)


def build_app(
    settings: Settings | None = None,
    demo_mode: bool = False,
    override_listener: AudioListener | None = None,
    override_speaker: AudioSpeaker | None = None,
    override_weather_provider: WeatherProvider | None = None,
    override_email_provider: EmailProvider | None = None,
    override_knowledge_provider: KnowledgeProvider | None = None,
) -> VoiceAssistantApp:
    """Build and wire all dependencies for the VoiceAssistantApp."""
    app_settings = settings or Settings.load()

    # 1. Audio Components
    if override_listener:
        listener = override_listener
    elif demo_mode:
        listener = ConsoleAudioListener()
    else:
        try:
            listener = SpeechRecognitionListener(app_settings.audio)
        except Exception as e:
            logger.warning(f"Microphone unavailable ({e}). Falling back to console text mode.")
            listener = ConsoleAudioListener()

    if override_speaker:
        speaker = override_speaker
    elif demo_mode:
        speaker = ConsoleAudioSpeaker()
    else:
        try:
            speaker = Pyttsx3Speaker(app_settings.audio)
        except Exception as e:
            logger.warning(f"TTS Engine unavailable ({e}). Falling back to console speaker.")
            speaker = ConsoleAudioSpeaker()

    # 2. NLP Pipeline
    classifier = HybridIntentClassifier(
        confidence_threshold=app_settings.nlp.confidence_threshold
    )
    nlu_parser = NLUParser(
        classifier=classifier,
        confidence_threshold=app_settings.nlp.confidence_threshold,
    )

    # 3. Storage
    storage_path = app_settings.storage.commands_path
    custom_storage = CustomCommandsStorage(storage_path)

    # 4. External Services
    # Weather
    if override_weather_provider:
        weather_provider = override_weather_provider
    elif app_settings.weather.is_configured:
        geocoder = OpenWeatherMapGeocoder(
            api_key=app_settings.weather.api_key,
            timeout=app_settings.weather.http_timeout,
        )
        weather_client = OpenWeatherMapClient(
            settings=app_settings.weather,
            geocoder=geocoder,
        )
        weather_provider = OpenWeatherMapProvider(weather_client)
    else:
        logger.info("OpenWeatherMap API key not provided. Initializing Mock/Fallback Weather Provider.")
        weather_provider = MockWeatherProvider()

    weather_service = WeatherService(weather_provider)

    # Email
    if override_email_provider:
        email_provider = override_email_provider
    elif app_settings.smtp.is_configured:
        email_client = SMTPEmailClient(app_settings.smtp)
        email_provider = SMTPEmailProvider(email_client)
    else:
        from voice_assistant.services.email.provider import MockEmailProvider
        logger.info("SMTP credentials not provided. Initializing Mock Email Provider.")
        email_provider = MockEmailProvider()

    email_service = EmailService(email_provider)

    # Reminders
    reminder_scheduler = ReminderScheduler()

    # Knowledge
    if override_knowledge_provider:
        knowledge_provider = override_knowledge_provider
    else:
        wiki_client = WikipediaKnowledgeClient(timeout=app_settings.weather.http_timeout)
        ddg_client = DuckDuckGoKnowledgeClient(timeout=app_settings.weather.http_timeout)
        local_curated = LocalCuratedKnowledgeProvider()
        knowledge_provider = CompositeKnowledgeProvider(
            wiki_client=wiki_client,
            ddg_client=ddg_client,
            local_provider=local_curated,
        )

    knowledge_service = KnowledgeService(knowledge_provider)

    # 5. Session Manager
    session_manager = SessionManager(default_timeout=60.0)

    # 6. Command Registry & Commands Wiring
    registry = CommandRegistry()
    registry.register(GreetingCommand())
    registry.register(DateTimeCommand())
    registry.register(WebSearchCommand())
    registry.register(WeatherCommand(weather_service))
    registry.register(ReminderCommand(reminder_scheduler))
    registry.register(EmailCommand(email_service, session_manager))
    registry.register(KnowledgeCommand(knowledge_service))
    registry.register(CustomCommandsCommand(custom_storage))
    registry.register(HelpCommand())
    registry.register(ExitCommand())
    registry.register(CancelCommand(session_manager))

    # 7. Lifecycle
    lifecycle = LifecycleManager()

    # 8. App Assembly
    return VoiceAssistantApp(
        settings=app_settings,
        listener=listener,
        speaker=speaker,
        nlu_parser=nlu_parser,
        command_registry=registry,
        session_manager=session_manager,
        custom_storage=custom_storage,
        reminder_scheduler=reminder_scheduler,
        lifecycle=lifecycle,
    )
