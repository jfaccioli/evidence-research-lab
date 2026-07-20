"""Simple daily call budget."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class RateLimiter:
    max_calls_per_day: int = 50
    _day: date = field(default_factory=date.today)
    _count: int = 0

    def allow(self) -> bool:
        today = date.today()
        if today != self._day:
            self._day = today
            self._count = 0
        if self._count >= self.max_calls_per_day:
            return False
        self._count += 1
        return True
