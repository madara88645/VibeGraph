"""In-memory metering for server-funded AI trial requests."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from threading import Lock


class TrialMeter:
    """Track per-identity allowance and a process-local daily global cap."""

    def __init__(
        self,
        free_calls: int = 5,
        global_daily_cap: int = 500,
        *,
        today: Callable[[], date] = date.today,
    ) -> None:
        self.free_calls = max(0, free_calls)
        self.global_daily_cap = max(0, global_daily_cap)
        self._today = today
        self._day = today()
        self._used_by_identity: dict[str, int] = {}
        self._global_used = 0
        self._lock = Lock()

    def remaining(self, identity: str) -> int:
        """Return remaining trial calls, taking the global cap into account."""
        with self._lock:
            self._roll_day_if_needed()
            return self._remaining_unlocked(identity)

    def consume(self, identity: str) -> int:
        """Consume one call when available and return the new remaining value."""
        _, remaining = self.consume_if_available(identity)
        return remaining

    def consume_if_available(self, identity: str) -> tuple[bool, int]:
        """Atomically consume one call and report whether funding was granted."""
        with self._lock:
            self._roll_day_if_needed()
            if self._remaining_unlocked(identity) <= 0:
                return False, 0

            self._used_by_identity[identity] = (
                self._used_by_identity.get(identity, 0) + 1
            )
            self._global_used += 1
            return True, self._remaining_unlocked(identity)

    def is_global_exhausted(self) -> bool:
        """Return whether the process-local daily funding cap is exhausted."""
        with self._lock:
            self._roll_day_if_needed()
            return self._global_used >= self.global_daily_cap

    def _remaining_unlocked(self, identity: str) -> int:
        if self._global_used >= self.global_daily_cap:
            return 0
        used = self._used_by_identity.get(identity, 0)
        return max(0, self.free_calls - used)

    def _roll_day_if_needed(self) -> None:
        current_day = self._today()
        if current_day == self._day:
            return
        self._day = current_day
        self._used_by_identity.clear()
        self._global_used = 0
