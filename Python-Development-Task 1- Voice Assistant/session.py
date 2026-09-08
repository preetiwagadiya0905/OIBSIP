"""Conversational multi-turn session state machine and manager."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from voice_assistant.observability.logging import get_logger

logger = get_logger(__name__)


class SessionStep(str, Enum):
    """Workflow steps for conversational commands."""
    AWAITING_RECIPIENT = "AWAITING_RECIPIENT"
    AWAITING_SUBJECT = "AWAITING_SUBJECT"
    AWAITING_BODY = "AWAITING_BODY"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    AWAITING_CUSTOM_TARGET = "AWAITING_CUSTOM_TARGET"


@dataclass
class ConversationSession:
    """Represents an active multi-turn conversation session."""
    session_type: str
    current_step: SessionStep
    data: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    timeout_seconds: float = 60.0

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.last_activity) > self.timeout_seconds

    def touch(self) -> None:
        self.last_activity = time.time()


class SessionManager:
    """Manages active conversation session state and transitions."""

    def __init__(self, default_timeout: float = 60.0):
        self.default_timeout = default_timeout
        self._active_session: ConversationSession | None = None

    @property
    def has_active_session(self) -> bool:
        """Check if an active, unexpired session exists."""
        if not self._active_session:
            return False
        if self._active_session.is_expired:
            logger.info(f"Session '{self._active_session.session_type}' timed out and was cleared.")
            self._active_session = None
            return False
        return True

    @property
    def current_session(self) -> ConversationSession | None:
        if self.has_active_session:
            return self._active_session
        return None

    def start_session(
        self, session_type: str, initial_step: SessionStep, data: dict[str, Any] | None = None
    ) -> ConversationSession:
        """Begin a new conversation session."""
        session = ConversationSession(
            session_type=session_type,
            current_step=initial_step,
            data=data or {},
            timeout_seconds=self.default_timeout,
        )
        self._active_session = session
        logger.info(f"Started multi-turn session '{session_type}' at step {initial_step.value}")
        return session

    def advance_step(self, next_step: SessionStep, update_data: dict[str, Any] | None = None) -> None:
        """Advance active session to next step."""
        if self._active_session:
            self._active_session.current_step = next_step
            if update_data:
                self._active_session.data.update(update_data)
            self._active_session.touch()
            logger.debug(f"Session '{self._active_session.session_type}' advanced to {next_step.value}")

    def clear(self) -> None:
        """Safely clear active session."""
        if self._active_session:
            logger.info(f"Cleared active session '{self._active_session.session_type}'")
        self._active_session = None
