import time
import inspect
from typing import Callable, Coroutine, Awaitable, Union, TypeVar, ParamSpec, Any

P = ParamSpec("P")
RT = TypeVar("RT")


class TimerBase:
    _running: bool = False
    _current_time: float = 0
    _start_intervals: list[float] = []
    _pause_intervals: list[float] = []

    def _reset_intervals(self):
        self._pause_intervals = []
        self._start_intervals = []

    def _get_timestamp(self) -> float:
        time_ms = time.time_ns() / 1_000_000
        return time_ms

    def _append_start_interval(self, diff: float = 0):
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

    def _calculate_intervals(self) -> float:
        total_diff = 0
        for paused_at, started_At in zip(self._pause_intervals, self._start_intervals):
            diff = paused_at - started_At
            total_diff += diff
        return total_diff

    def _get_last_interval(self) -> float:
        return self._get_timestamp() - self._start_intervals[-1]

    def _calculate_time(self):
        if not self._running:
            return

        if self._start_intervals and self._pause_intervals:
            interval_diff = self._calculate_intervals()

            if len(self._pause_intervals) != len(self._start_intervals):
                interval_diff += self._get_last_interval()

            self._current_time = interval_diff
            self._refresh_start_intervals()
            self._clear_pause_intervals()

        elif self._start_intervals and not self._pause_intervals:
            interval_diff = self._get_last_interval()
            self._current_time = interval_diff
            self._refresh_start_intervals()


class TimerModule(TimerBase):
    def __init__(self):
        super().__init__()

    def start_time(self):
        if not self._running:
            self._reset_intervals()
            self._append_start_interval(self._current_time)
            self._calculate_time()
        self._running = True
        return self

    def pause_time(self):
        if self._running:
            self._append_pause_interval()
            self._calculate_time()
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

    def set_time(self, time_sec: int):
        self._current_time = time_sec * 1000
        self._append_start_interval(self._current_time)
        self._calculate_time()
        return self

    def get_time(self) -> float:
        self._calculate_time()
        time_sec = self._current_time / 1000
        return time_sec

    def get_time_ms(self) -> float:
        self._calculate_time()
        return self._current_time


class TimeProfilerBase:
    def __init__(self):
        self._timer_refs = {}

    @staticmethod
    def _create_timer() -> TimerModule:
        timer = TimerModule().start_time()
        return timer

    def _complete_timer(self, function: Callable, timer: TimerModule) -> None:
        function_name = function.__qualname__
        time_taken = timer.get_time_ms()
        print("=========")
        print(f"Name: {function_name}\nTime Taken: [{time_taken}ms]")
        if function not in self._timer_refs:
            self._timer_refs.update({function: 0})
        self._timer_refs[function] += time_taken

    def _set_attribute(self, class_instance: object, name: str, method: Any):
        try:
            class_instance.__setattr__(name, method)
        except AttributeError:
            print(f"Class Method ({name}) is read-only and cannot be timed.")


class TimeProfiler(TimeProfilerBase):
    def get_method_wrapper(
        self, method: Callable[P, RT]
    ) -> Union[Callable[..., RT], Callable[..., Coroutine[Any, Any, RT]]]:
        is_coroutine = inspect.iscoroutinefunction(method)
        if is_coroutine:
            return self.async_function_decorator(method)
        return self.function_decorator(method)

    def class_decorator(self, class_object: Callable[P, RT]) -> Callable[..., RT]:
        def class_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            class_instance = class_object(*args, **kwargs)
            methods = inspect.getmembers(class_instance, predicate=inspect.ismethod)
            for name, method in methods:
                method = self.get_method_wrapper(method)
                self._set_attribute(class_instance, name, method)

            return class_instance

        return class_wrapper

    def function_decorator(self, func: Callable[P, RT]) -> Callable[..., RT]:
        def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            timer = self._create_timer()
            func_return = func(*args, **kwargs)
            self._complete_timer(func, timer)
            return func_return

        return function_wrapper

    def async_function_decorator(
        self, func: Callable[P, Awaitable[RT]]
    ) -> Callable[..., Coroutine[Any, Any, RT]]:
        async def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            timer = self._create_timer()
            func_return = await func(*args, **kwargs)
            self._complete_timer(func, timer)
            return func_return

        return function_wrapper
