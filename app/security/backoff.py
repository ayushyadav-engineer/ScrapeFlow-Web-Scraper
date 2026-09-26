from __future__ import annotations

import threading
import time


class ExponentialBackoff:
    """Non-locking exponential delay tracker with configurable reset/retention."""

    def __init__(self, base: float, maximum: float, reset_after: float = 900.0):
        self.base = max(0.1, base)
        self.maximum = max(self.base, maximum)
        self.reset_after = max(1.0, reset_after)
        self._lock = threading.Lock()
        self._state: dict[str, tuple[int, float]] = {}

    def _get(self, key: str) -> tuple[int, float]:
        attempts, last = self._state.get(key, (0, 0.0))
        if attempts and time.time() - last >= self.reset_after:
            self._state.pop(key, None)
            return 0, 0.0
        return attempts, last

    def delay_for(self, key: str) -> float:
        with self._lock:
            attempts, _ = self._get(key)
            if attempts <= 0:
                return 0.0
            return min(self.maximum, self.base * (2 ** (attempts - 1)))

    def failed(self, key: str):
        with self._lock:
            attempts, _ = self._get(key)
            self._state[key] = (min(attempts + 1, 10), time.time())

    def succeeded(self, key: str):
        with self._lock:
            self._state.pop(key, None)
