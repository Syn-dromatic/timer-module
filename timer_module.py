import time
import inspect
from typing import Callable, Awaitable
from typing import Union, Type, TypeVar, ParamSpec


P = ParamSpec("P")
RT = TypeVar("RT")
CT = TypeVar("CT")


class TimerModule:
    __slots__ = ["is_running", "st_time", "cr_time"]

    def __init__(self):
        self.is_running: bool = False
        self.st_time: float = 0
        self.cr_time: float = 0

    @staticmethod
    def get_timestamp_ms() -> float:
        time_ms = time.time_ns() / 1_000_000
        return time_ms

    def start(self):
        if not self.is_running:
            self.st_time = self.get_timestamp_ms() - self.cr_time
        self.is_running = True
        return self

    def pause(self):
        if self.is_running:
            self.cr_time = self.get_timestamp_ms() - self.st_time
        self.is_running = False
        return self

    def reset(self):
        self.st_time = 0
        self.cr_time = 0
        self.is_running = False
        return self

    def refresh(self):
        self.reset()
        self.start()
        return self

    def set_time(self, time_sec: int):
        self.cr_time = time_sec * 1000
        self.st_time = self.get_timestamp_ms() - self.cr_time
        return self

    def get_time(self) -> float:
        if self.is_running:
            self.cr_time = self.get_timestamp_ms() - self.st_time
        time_sec = self.cr_time / 1000
        return time_sec

    def get_time_ms(self) -> float:
        if self.is_running:
            self.cr_time = self.get_timestamp_ms() - self.st_time
        return self.cr_time


class TimeProfilerBase:
    __slots__ = [
        "_realtime",
        "_prof_timing_refs",
        "_prof_timing_total",
        "_object_refs",
        "_ref_idx",
        "_pcall_idx",
        "_pcall_set",
    ]

    def __init__(self, realtime: bool = False):
        self._realtime: bool = realtime
        self._prof_timing_refs: dict[str, dict[str, float]] = {}
        self._prof_timing_total: float = 0
        self._object_refs: dict[str, int] = {}
        self._ref_idx: int = 0
        self._pcall_idx: int = 0
        self._pcall_set: bool = False

    def __del__(self):
        self._pcall_idx = 0
        report_str = "END REPORT"
        print(f"{'=' * len(report_str)}\n{report_str}\n{'=' * len(report_str)}\n")
        self._profiling_report()

    @staticmethod
    def _create_timer_module() -> TimerModule:
        return TimerModule()

    @staticmethod
    def _get_object_name(obj: Callable):
        obj_module = obj.__module__
        obj_name = obj.__qualname__
        return f"{obj_module}.{obj_name}"

    @staticmethod
    def _set_attribute(instance: CT, name: str, method: Callable) -> CT:
        try:
            instance.__setattr__(name, method)
        except AttributeError:
            print(f"Class Method ({name}) is read-only and cannot be timed.")
        return instance

    def _get_pcall_total_time(self, pcall: str) -> float:
        pcall_total_time = 0
        for obj, obj_time in self._prof_timing_refs[pcall].items():
            if pcall == obj:
                pcall_total_time += obj_time
        return pcall_total_time

    def _add_object_ref(self, obj: Callable):
        obj_name = self._get_object_name(obj)
        if obj_name not in self._object_refs:
            self._object_refs.update({obj_name: self._ref_idx})
            self._ref_idx += 1

    def _append_object_profiling(self, obj: Callable, time_taken: float) -> None:
        pcall_name = list(self._object_refs.keys())[self._pcall_idx]
        obj_name = self._get_object_name(obj)

        if pcall_name not in self._prof_timing_refs:
            self._prof_timing_refs.update({pcall_name: {}})

        if obj_name not in self._prof_timing_refs[pcall_name]:
            self._prof_timing_refs[pcall_name].update({obj_name: 0})

        self._prof_timing_refs[pcall_name][obj_name] += time_taken

        is_pcall = self._object_refs[obj_name] == self._pcall_idx
        if is_pcall:
            self._prof_timing_total += time_taken
            self._pcall_set = False

        if is_pcall and self._realtime:
            self._profiling_report()

    def _profiling_report(self):
        for pcall, pcall_objs in self._prof_timing_refs.items():
            profile_header = f"█ PROFILE: {pcall} █"
            header_len = len(profile_header)
            print(f"\n{profile_header}\n" f"{'=' * header_len}")
            pcall_total_time = self._get_pcall_total_time(pcall)
            for obj, obj_time in pcall_objs.items():
                if obj == pcall:
                    continue
                t_prc = 0
                if obj_time != 0 and pcall_total_time != 0:
                    t_prc = (obj_time / pcall_total_time) * 100

                print(
                    f"Name: {obj}\n"
                    f"Time: [{obj_time:.2f}ms] — T%: {t_prc:.2f}%\n"
                    "——"
                )

            print(f"Profile Time: [{pcall_total_time:.2f}ms]\n")

        print(f"――― Total Time: [{self._prof_timing_total:.2f}ms] ―――\n\n\n")

    def _set_call_idx(self, obj: Callable):
        obj_name = self._get_object_name(obj)
        if not self._pcall_set:
            self._pcall_idx = self._object_refs[obj_name]
            self._pcall_set = True

    def _get_method_wrapper(
        self, method: Callable[P, RT]
    ) -> Union[Callable[P, RT], Callable[P, Awaitable[RT]]]:
        is_coroutine = inspect.iscoroutinefunction(method)
        timer_module = self._create_timer_module()
        if is_coroutine:
            return self._async_function_wrapper(method, timer_module)
        return self._function_wrapper(method, timer_module)

    def _class_wrapper(
        self, c_obj: Type[Callable[P, CT]], timer_module: TimerModule
    ) -> Type[Callable[P, CT]]:
        class ClassWrapper:
            def __new__(cls: Type[c_obj], *args: P.args, **kwargs: P.kwargs) -> CT:
                self._set_call_idx(c_obj)
                timer_module.start()
                c_instance = c_obj(*args, **kwargs)
                time_ms = timer_module.get_time_ms()
                timer_module.reset()
                self._append_object_profiling(c_obj, time_ms)

                methods = inspect.getmembers(c_instance, predicate=inspect.ismethod)
                for name, method in methods:
                    self._add_object_ref(method)
                    method = self._get_method_wrapper(method)
                    c_instance = self._set_attribute(c_instance, name, method)
                return c_instance

        return ClassWrapper

    def _function_wrapper(
        self, func: Callable[P, RT], timer_module: TimerModule
    ) -> Callable[P, RT]:
        def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            self._set_call_idx(func)
            timer_module.start()
            func_return = func(*args, **kwargs)
            time_ms = timer_module.get_time_ms()
            timer_module.reset()
            self._append_object_profiling(func, time_ms)
            return func_return

        return function_wrapper

    def _async_function_wrapper(
        self, func: Callable[P, Awaitable[RT]], timer_module: TimerModule
    ) -> Callable[P, Awaitable[RT]]:
        async def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            self._set_call_idx(func)
            timer_module.start()
            func_return = await func(*args, **kwargs)
            time_ms = timer_module.get_time_ms()
            timer_module.reset()
            self._append_object_profiling(func, time_ms)
            return func_return

        return function_wrapper


class TimeProfiler(TimeProfilerBase):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance") or not isinstance(cls.instance, cls):
            cls.instance = super(TimeProfiler, cls).__new__(cls)
            super(cls, cls.instance).__init__(*args, **kwargs)
            TimeProfiler.__init__ = lambda *args, **kwargs: None
        return cls.instance

    def class_profiler(
        self, c_obj: Type[Callable[P, CT]]
    ) -> Union[Type[Callable[P, CT]], Type[CT]]:
        self._add_object_ref(c_obj)
        timer_module = self._create_timer_module()
        return self._class_wrapper(c_obj, timer_module)

    def function_profiler(self, func: Callable[P, RT]) -> Callable[P, RT]:
        self._add_object_ref(func)
        timer_module = self._create_timer_module()
        return self._function_wrapper(func, timer_module)

    def async_function_profiler(
        self, func: Callable[P, Awaitable[RT]]
    ) -> Callable[P, Awaitable[RT]]:
        self._add_object_ref(func)
        timer_module = self._create_timer_module()
        return self._async_function_wrapper(func, timer_module)
