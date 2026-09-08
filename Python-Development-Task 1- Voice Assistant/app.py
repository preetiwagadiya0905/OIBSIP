"""Main Voice Assistant application orchestrator."""

import threading

from voice_assistant.application.lifecycle import LifecycleManager
from voice_assistant.application.session import SessionManager
from voice_assistant.audio.listener import AudioListener
from voice_assistant.audio.speaker import AudioSpeaker
from voice_assistant.commands.base import CommandContext, CommandResult
from voice_assistant.commands.custom import CustomCommandsCommand
from voice_assistant.commands.registry import CommandRegistry
from voice_assistant.config.constants import AppState, IntentType
from voice_assistant.config.settings import Settings
from voice_assistant.errors.exceptions import (
    AudioError,
    CommandNotFoundError,
    SpeechTimeoutError,
    UnknownSpeechError,
)
from voice_assistant.nlp.intent import IntentResult
from voice_assistant.nlp.parser import NLUParser
from voice_assistant.observability.logging import get_logger
from voice_assistant.services.reminders.models import Reminder
from voice_assistant.services.reminders.scheduler import ReminderScheduler
from voice_assistant.storage.custom_commands import CustomCommandsStorage

logger = get_logger(__name__)


class VoiceAssistantApp:
    """Production application orchestrator coordinating speech, NLU, commands, and state."""

    def __init__(
        self,
        settings: Settings,
        listener: AudioListener,
        speaker: AudioSpeaker,
        nlu_parser: NLUParser,
        command_registry: CommandRegistry,
        session_manager: SessionManager,
        custom_storage: CustomCommandsStorage,
        reminder_scheduler: ReminderScheduler,
        lifecycle: LifecycleManager | None = None,
    ):
        self.settings = settings
        self.listener = listener
        self.speaker = speaker
        self.nlu_parser = nlu_parser
        self.command_registry = command_registry
        self.session_manager = session_manager
        self.custom_storage = custom_storage
        self.reminder_scheduler = reminder_scheduler
        self.lifecycle = lifecycle or LifecycleManager()

        self._state: AppState = AppState.IDLE
        self._running: bool = False
        self._lock = threading.Lock()

        # Connect reminder callback to voice speaker
        self.reminder_scheduler.set_alert_callback(self._on_reminder_alert)

        # Register shutdown cleanup
        self.lifecycle.register_shutdown_hook(self.shutdown)

    @property
    def state(self) -> AppState:
        return self._state

    def _set_state(self, new_state: AppState) -> None:
        self._state = new_state
        logger.debug(f"Application state transition: {new_state.value}")

    def _on_reminder_alert(self, reminder: Reminder) -> None:
        """Audible & spoken notification triggered when a reminder expires."""
        alert_text = f"Reminder: {reminder.message}"
        logger.info(f"Speaking reminder alert: '{alert_text}'")
        try:
            self.speaker.speak(alert_text)
        except Exception as e:
            logger.error(f"Failed to speak reminder alert: {e}")

    def start(self) -> None:
        """Start the assistant application."""
        logger.info(f"Starting {self.settings.app_name} (Environment: {self.settings.app_env.value})...")
        self._running = True
        self._set_state(AppState.IDLE)

        # Ambient noise calibration for microphone if supported
        try:
            self.listener.calibrate_noise(duration=1.0)
        except Exception as e:
            logger.warning(f"Microphone noise calibration skipped: {e}")

        # Initial welcome speech
        welcome = "Hello! I am Aura. How can I help you today?"
        self.speaker.speak(welcome)

    def process_utterance(self, text: str) -> CommandResult:
        """Process a single text/speech command utterance end-to-end and speak response."""
        self._set_state(AppState.PROCESSING)
        raw_text = text.strip()
        logger.info(f"Processing user input: '{raw_text}'")

        context = CommandContext(
            services={
                "settings": self.settings,
                "speaker": self.speaker,
                "listener": self.listener,
                "session_manager": self.session_manager,
                "custom_storage": self.custom_storage,
                "reminder_scheduler": self.reminder_scheduler,
            },
            app_state=self._state,
        )

        # 1. If an active conversational session is ongoing, route input directly to it
        if self.session_manager.has_active_session:
            session = self.session_manager.current_session
            if session:
                self._set_state(AppState.CONFIRMING)
                intent_result = self.nlu_parser.parse(raw_text)
                if intent_result.intent == IntentType.CANCEL:
                    self.session_manager.clear()
                    result = CommandResult.ok("Operation cancelled.")
                else:
                    try:
                        cmd = self.command_registry.get_command(IntentType.SEND_EMAIL)
                        result = cmd.execute(intent_result, context)
                    except Exception as e:
                        logger.error(f"Session processing error: {e}")
                        result = CommandResult.fail("Could not process conversational input.")

                self.speaker.speak(result.response_text)
                self._set_state(AppState.IDLE)
                return result

        # 2. Check registered custom commands first for exact triggers
        custom_cmd = self.custom_storage.get_command(raw_text)
        if custom_cmd:
            self._set_state(AppState.EXECUTING)
            custom_handler: CustomCommandsCommand = self.command_registry.get_command(IntentType.ADD_COMMAND)  # type: ignore
            result = custom_handler.try_execute_custom(raw_text)
            self.speaker.speak(result.response_text)
            self._set_state(AppState.IDLE)
            return result

        # 3. Parse intent with NLU pipeline
        intent_result: IntentResult = self.nlu_parser.parse(raw_text)

        # 4. Handle low-confidence clarification
        if intent_result.requires_clarification and intent_result.clarification_prompt:
            logger.info(f"Low confidence intent ({intent_result.confidence:.2f}). Asking for clarification.")
            self.speaker.speak(intent_result.clarification_prompt)
            self._set_state(AppState.IDLE)
            return CommandResult.ok(intent_result.clarification_prompt)

        # 5. Handle unrecognized / UNKNOWN intent
        if intent_result.intent == IntentType.UNKNOWN:
            msg = "I'm not sure how to help with that yet. Try saying 'help' to hear what I can do."
            self.speaker.speak(msg)
            self._set_state(AppState.IDLE)
            return CommandResult.fail(msg)

        # 6. Execute registered command
        self._set_state(AppState.EXECUTING)
        try:
            command = self.command_registry.get_command(intent_result.intent)
            result = command.execute(intent_result, context)
        except CommandNotFoundError:
            logger.warning(f"No command registered for intent: {intent_result.intent.value}")
            result = CommandResult.fail(
                "I recognize that intent, but no command is currently assigned to handle it."
            )
        except Exception as e:
            logger.error(f"Error executing command for {intent_result.intent.value}: {e}")
            result = CommandResult.fail(f"Sorry, an error occurred while processing your request: {e}")

        # 7. Speak response and handle exit flag
        self.speaker.speak(result.response_text)

        if result.should_exit:
            logger.info("Command requested application exit.")
            self._running = False
            self.shutdown()
            return result

        self._set_state(AppState.IDLE)
        return result

    def run_loop(self) -> None:
        """Main listening and execution loop."""
        self.start()
        logger.info("Voice assistant loop active. Listening for commands...")

        while self._running:
            try:
                self._set_state(AppState.LISTENING)
                transcription = self.listener.listen()
                if transcription:
                    self.process_utterance(transcription)

            except SpeechTimeoutError:
                # No speech detected during interval, continue listening silently
                continue

            except UnknownSpeechError:
                logger.info("Speech was detected but could not be recognized.")
                self.speaker.speak("I didn't catch that. Please try again.")

            except AudioError as e:
                logger.error(f"Audio listening error: {e}")
                self.speaker.speak("I'm having trouble with the audio input. Please check your microphone.")

            except (KeyboardInterrupt, SystemExit):
                logger.info("Interrupted by user. Exiting loop.")
                break

            except Exception as e:
                logger.error(f"Unexpected error in voice loop: {e}")
                self.speaker.speak("An unexpected error occurred. Please try again.")

        self.shutdown()

    def shutdown(self) -> None:
        """Gracefully release all audio, scheduler, and worker resources."""
        with self._lock:
            if self._state == AppState.SHUTTING_DOWN:
                return
            self._set_state(AppState.SHUTTING_DOWN)
            self._running = False

        logger.info("Shutting down Voice Assistant application...")
        self.reminder_scheduler.shutdown()
        self.speaker.shutdown()
        logger.info("Voice Assistant shutdown complete.")
