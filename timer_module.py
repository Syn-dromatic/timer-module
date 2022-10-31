import time
from typing import Union, Type


class TimerBase:
    _timestamp_type: Union[Type[int], Type[float]] = int
    _running: bool = False
    _current_time: Union[int, float] = 0
    _start_intervals: list[Union[int, float]] = []
    _pause_intervals: list[Union[int, float]] = []

    def _reset_intervals(self):
        self._pause_intervals = []
        self._start_intervals = []

    def _get_timestamp(self) -> Union[int, float]:
        timestamp = self._timestamp_type(time.time())
        return timestamp

    def _append_start_interval(self, diff: Union[int, float] = 0):
        timestamp = self._get_timestamp()
        self._start_intervals.append(timestamp - diff)

    def _append_pause_interval(self):
        timestamp = self._get_timestamp()
        self._pause_intervals.append(timestamp)

    def _refresh_start_intervals(self):
        self._start_intervals = []
        self._append_start_interval(diff=self._current_time)

    def _clear_pause_intervals(self):
        self._pause_intervals = []

    def _calculate_time(self):
        if not self._running:
            return

        if self._start_intervals and self._pause_intervals:
            cur_time = sum([(paused_at - started_at) for (paused_at, started_at)
                            in zip(self._pause_intervals, self._start_intervals)])

            if len(self._pause_intervals) != len(self._start_intervals):
                cur_time += (self._get_timestamp() - self._start_intervals[-1])

            self._current_time = cur_time
            self._refresh_start_intervals()
            self._clear_pause_intervals()

        elif self._start_intervals and not self._pause_intervals:
            cur_time = (self._get_timestamp() - self._start_intervals[-1])
            self._current_time = cur_time
            self._refresh_start_intervals()


class TimerModule(TimerBase):
    def __init__(self, tstmp_type=TimerBase._timestamp_type):
        super().__init__()
        self._timestamp_type = tstmp_type

    def start_time(self):
        if not self._running:
            self._reset_intervals()
            self._append_start_interval(self._current_time)
            self.get_time()
        self._running = True
        return self

    def pause_time(self):
        if self._running:
            self.get_time()
            self._append_pause_interval()
        self._running = False
        return self

    def reset_time(self):
        self._current_time = 0
        self._running = False
        self._start_intervals = []
        self._pause_intervals = []
        return self

    def refresh_time(self):
        self.reset_time()
        self.start_time()
        return self

    def set_time(self, time: Union[int, float]):
        self._current_time = time
        self._append_start_interval(self._current_time)
        self.get_time()
        return self

    def get_time(self) -> Union[int, float]:
        self._calculate_time()
        return self._current_time
