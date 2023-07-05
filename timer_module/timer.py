import time
from typing import Self

from .metrics import TimeFormatterNs


class TimerModuleBase:
    __slots__ = ["_is_running", "_st_time_ns", "_cr_time_ns"]

    def __init__(self):
        self._is_running: bool = False
        self._st_time_ns: float = 0.0
        self._cr_time_ns: float = 0.0

    @staticmethod
    def _get_time_ns() -> float:
        time_ms = time.time_ns()
        return time_ms

    def _set_time_ns(self, nanoseconds: float):
        self._cr_time_ns = nanoseconds
        self._st_time_ns = self._get_time_ns() - nanoseconds

    def _set_start_time(self):
        self._st_time_ns = self._get_time_ns() - self._cr_time_ns

    def _set_current_time(self):
        self._cr_time_ns = self._get_time_ns() - self._st_time_ns

    def _update_start_time(self):
        if not self._is_running:
            self._set_start_time()

    def _update_current_time(self):
        if self._is_running:
            self._set_current_time()


class TimerModule(TimerModuleBase):
    def __init__(self) -> None:
        super().__init__()

    def __repr__(self) -> str:
        self._update_current_time()
        formatter = TimeFormatterNs(self._cr_time_ns)
        return formatter.auto_format()

    def start(self) -> Self:
        self._update_start_time()
        self._is_running = True
        return self

    def pause(self) -> Self:
        self._update_current_time()
        self._is_running = False
        return self

    def reset(self) -> Self:
        self._cr_time_ns = 0.0
        self._st_time_ns = 0.0
        self._is_running = False
        return self

    def refresh(self) -> Self:
        self._cr_time_ns = 0.0
        self._set_start_time()
        return self

    def set_time(self, seconds: float) -> Self:
        nanoseconds = seconds * 1e9
        self._set_time_ns(nanoseconds)
        return self

    def set_time_ms(self, milliseconds: float) -> Self:
        nanoseconds = milliseconds * 1e6
        self._set_time_ns(nanoseconds)
        return self

    def set_time_ns(self, nanoseconds: float) -> Self:
        self._set_time_ns(nanoseconds)
        return self

    def get_time(self) -> float:
        self._update_current_time()
        time_sec = self._cr_time_ns / 1e9
        return time_sec

    def get_time_ms(self) -> float:
        self._update_current_time()
        time_ms = self._cr_time_ns / 1e6
        return time_ms

    def get_time_ns(self) -> float:
        self._update_current_time()
        return self._cr_time_ns
