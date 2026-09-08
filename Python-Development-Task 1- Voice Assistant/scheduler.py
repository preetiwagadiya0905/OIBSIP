"""Asynchronous, non-blocking reminder scheduler."""

import threading
from collections.abc import Callable
from datetime import datetime, timezone

from voice_assistant.config.constants import (
    MAX_REMINDER_DURATION_SECONDS,
    MIN_REMINDER_DURATION_SECONDS,
    ReminderStatus,
)
from voice_assistant.errors.exceptions import ReminderError
from voice_assistant.observability.logging import get_logger
from voice_assistant.services.reminders.models import Reminder
from voice_assistant.utils.sound import play_chime_async

logger = get_logger(__name__)


class ReminderScheduler:
    """Thread-safe background reminder scheduler."""

    def __init__(self, alert_callback: Callable[[Reminder], None] | None = None):
        self.alert_callback = alert_callback
        self._reminders: dict[str, Reminder] = {}
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def set_alert_callback(self, callback: Callable[[Reminder], None]) -> None:
        """Register the speaker callback to trigger when reminders fire."""
        self.alert_callback = callback

    def schedule(self, duration_seconds: int, message: str) -> Reminder:
        """Schedule a new reminder asynchronously."""
        if not (MIN_REMINDER_DURATION_SECONDS <= duration_seconds <= MAX_REMINDER_DURATION_SECONDS):
            raise ReminderError(
                f"Reminder duration must be between {MIN_REMINDER_DURATION_SECONDS}s "
                f"and {MAX_REMINDER_DURATION_SECONDS // 86400} days."
            )

        clean_message = message.strip() if message else "Reminder alert"
        reminder = Reminder(duration_seconds=duration_seconds, message=clean_message)

        timer = threading.Timer(
            interval=float(duration_seconds),
            function=self._on_timer_fired,
            args=[reminder.id],
        )
        timer.daemon = True

        with self._lock:
            self._reminders[reminder.id] = reminder
            self._timers[reminder.id] = timer

        timer.start()
        logger.info(
            f"Scheduled reminder [id={reminder.id}] in {reminder.human_duration} for '{reminder.message}'"
        )
        return reminder

    def _on_timer_fired(self, reminder_id: str) -> None:
        """Callback executed on background thread when a reminder expires."""
        with self._lock:
            reminder = self._reminders.get(reminder_id)
            if not reminder or reminder.status != ReminderStatus.SCHEDULED:
                return
            reminder.status = ReminderStatus.COMPLETED
            reminder.completed_at = datetime.now(timezone.utc)
            self._timers.pop(reminder_id, None)

        logger.info(f"Reminder triggered [id={reminder.id}]: '{reminder.message}'")

        # 1. Play audible chime alert
        play_chime_async()

        # 2. Invoke alert callback (e.g. speak the reminder aloud)
        if self.alert_callback:
            try:
                self.alert_callback(reminder)
            except Exception as e:
                logger.error(f"Failed to execute alert callback for reminder {reminder.id}: {e}")

    def cancel(self, reminder_id: str | None = None) -> bool:
        """Cancel a reminder by ID, or cancel the most recently scheduled one if none specified."""
        with self._lock:
            target_id = reminder_id
            if not target_id:
                # Find most recent scheduled reminder
                scheduled = [r for r in self._reminders.values() if r.status == ReminderStatus.SCHEDULED]
                if not scheduled:
                    return False
                target_id = scheduled[-1].id

            reminder = self._reminders.get(target_id)
            timer = self._timers.pop(target_id, None)

            if timer:
                timer.cancel()

            if reminder and reminder.status == ReminderStatus.SCHEDULED:
                reminder.status = ReminderStatus.CANCELLED
                logger.info(f"Cancelled reminder [id={reminder.id}]")
                return True

            return False

    def list_active(self) -> list[Reminder]:
        """Return list of all currently active/scheduled reminders."""
        with self._lock:
            return [
                r for r in self._reminders.values() if r.status == ReminderStatus.SCHEDULED
            ]

    def shutdown(self) -> None:
        """Cancel all running background timers cleanly."""
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
        logger.info("Reminder scheduler shutdown complete.")
