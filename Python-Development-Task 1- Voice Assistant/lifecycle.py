"""Application lifecycle and signal handling."""

import signal
import sys
from collections.abc import Callable

from voice_assistant.observability.logging import get_logger

logger = get_logger(__name__)


class LifecycleManager:
    """Handles application initialization, signal interception, and teardown."""

    def __init__(self) -> None:
        self._shutdown_callbacks: list[Callable[[], None]] = []
        self._is_shutting_down = False
        self._register_signals()

    def _register_signals(self) -> None:
        """Register OS interrupt signals."""
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except Exception as e:
            logger.debug(f"Could not register signal handlers (may be running in non-main thread): {e}")

    def _handle_signal(self, signum: int, frame: any) -> None:
        sig_name = signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
        logger.info(f"Received shutdown signal {sig_name}. Initiating graceful exit...")
        self.shutdown()
        sys.exit(0)

    def register_shutdown_hook(self, callback: Callable[[], None]) -> None:
        """Register a cleanup hook to execute upon shutdown."""
        self._shutdown_callbacks.append(callback)

    def shutdown(self) -> None:
        """Execute all registered teardown callbacks."""
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        logger.info("Executing lifecycle shutdown hooks...")
        for callback in reversed(self._shutdown_callbacks):
            try:
                callback()
            except Exception as e:
                logger.error(f"Error during shutdown callback: {e}")
        logger.info("Application lifecycle shutdown complete.")
