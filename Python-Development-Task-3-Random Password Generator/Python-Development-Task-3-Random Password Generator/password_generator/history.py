"""In-memory session history management for generated passwords.

Maintains a bounded FIFO queue of the last 5 generated passwords strictly in memory.
No persistence, disk I/O, or logging is performed to guarantee user privacy.
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass(frozen=True)
class HistoryEntry:
    """An in-memory record of a generated password."""
    password: str
    strength_label: str
    strength_color: str
    timestamp: str


class SessionHistory:
    """Bounded, in-memory session history that stores up to max_entries items."""

    def __init__(self, max_entries: int = 5) -> None:
        self._max_entries = max_entries
        self._entries: deque[HistoryEntry] = deque(maxlen=max_entries)

    def add(self, password: str, strength_label: str, strength_color: str) -> None:
        """Add a newly generated password entry. Oldest entry is automatically dropped if > max_entries."""
        time_str = datetime.now().strftime("%H:%M:%S")
        entry = HistoryEntry(
            password=password,
            strength_label=strength_label,
            strength_color=strength_color,
            timestamp=time_str,
        )
        self._entries.append(entry)

    def get_entries(self) -> List[HistoryEntry]:
        """Return the list of history entries from newest to oldest."""
        # Reversed so the newest appears at the top of the UI list
        return list(reversed(self._entries))

    def clear(self) -> None:
        """Clear all session history from memory."""
        self._entries.clear()

    @property
    def count(self) -> int:
        """Return the number of entries currently stored."""
        return len(self._entries)
