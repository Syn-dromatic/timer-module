import time
import inspect
from dataclasses import dataclass
from typing import Callable, Awaitable
from typing import Union, Optional, Type, TypeVar, ParamSpec


P = ParamSpec("P")
RT = TypeVar("RT")
CT = TypeVar("CT")


@dataclass
class ObjectCall:
    obj: Callable
    name: str
    module: str
    time: float
    ncalls: int

    def __refname__(self):
        return f"{self.module}.{self.name}"

    def __hash__(self) -> int:
        return hash(self.__refname__())


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
    def __init__(self, realtime: bool = False):
        self._realtime: bool = realtime

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance") or not isinstance(cls.instance, cls):
            cls.instance = super(TimeProfilerBase, cls).__new__(cls)
            cls._prof_timing_refs: dict[ObjectCall, dict[Callable, ObjectCall]] = {}
            cls._prof_timing_total: float = 0
            cls._object_refs: dict[Callable, ObjectCall] = {}
            cls._pcall_obj: Optional[ObjectCall] = None
        return cls.instance

    def __del__(self):
        report_str = "END REPORT"
        print(f"{'=' * len(report_str)}\n{report_str}\n{'=' * len(report_str)}\n")
        self._profiling_report()

    @staticmethod
    def _create_timer_module() -> TimerModule:
        return TimerModule()

    @staticmethod
    def _create_object_call(obj: Callable):
        obj_name = obj.__qualname__
        obj_module = obj.__module__

        obj_call = ObjectCall(
            obj=obj,
            name=obj_name,
            module=obj_module,
            time=0,
            ncalls=0,
        )
        return obj_call

    @staticmethod
    def _set_attribute(instance: CT, name: str, method: Callable) -> CT:
        try:
            instance.__setattr__(name, method)
        except AttributeError:
            print(f"Class Method ({name}) is read-only and cannot be timed.")
        return instance

    def _add_object_ref(self, obj: Callable):
        obj_call = self._create_object_call(obj)
        if obj_call not in self._object_refs:
            self._object_refs.update({obj: obj_call})

    def _append_object_profiling(
        self, pcall_obj: ObjectCall, obj: Callable, time_taken: float
    ) -> None:
        obj_call = self._object_refs[obj]
        obj_call.time += time_taken
        obj_call.ncalls += 1
        self._prof_timing_refs[pcall_obj].update({obj: obj_call})

        is_pcall = obj_call == pcall_obj
        if is_pcall:
            self._prof_timing_total += time_taken
            self._pcall_obj = None

        if is_pcall and self._realtime:
            self._profiling_report()

    @staticmethod
    def _format_time(time: float):
        if time >= 0.01:
            return f"{time:.2f}ms"
        return f"{time*1000000:.2f}ns"

    @staticmethod
    def _print_pcall_header(obj_call: ObjectCall):
        pcall_name = obj_call.name
        profile_header = f"█ PROFILE: {pcall_name} █"
        header_len = len(profile_header)
        print(f"\n{profile_header}\n" f"{'=' * header_len}")

    def _print_pcall(self, obj_call: ObjectCall):
        pcall_time = obj_call.time
        pcall_ncalls = obj_call.ncalls
        pcall_percall = pcall_time / pcall_ncalls

        f_pcall_time = self._format_time(pcall_time)
        f_pcall_percall = self._format_time(pcall_percall)

        print(
            f"Profile Time: [{f_pcall_time}]\n"
            f"NCalls: [{pcall_ncalls}] — PerCall: [{f_pcall_percall}]\n"
            "——————\n"
        )

    def _print_call(self, obj_call: ObjectCall, pcall_time: float):
        obj_name = obj_call.name
        obj_time = obj_call.time

        obj_ncalls = obj_call.ncalls
        obj_percall = obj_time / obj_ncalls

        f_obj_time = self._format_time(obj_time)
        f_obj_percall = self._format_time(obj_percall)

        t_prc = 0
        if obj_time != 0 and pcall_time != 0:
            t_prc = (obj_time / pcall_time) * 100

        print(
            f"Name: {obj_name}\n"
            f"Time: [{f_obj_time}] — T%: {t_prc:.2f}%\n"
            f"NCalls: [{obj_ncalls}] — PerCall: [{f_obj_percall}]\n"
            "——"
        )

    def _profiling_report(self):
        for pcall_obj, obj_dict in self._prof_timing_refs.items():
            self._print_pcall_header(pcall_obj)
            pcall_time = pcall_obj.time
            for obj_call in obj_dict.values():
                if obj_call == pcall_obj:
                    continue
                self._print_call(obj_call, pcall_time)
            self._print_pcall(pcall_obj)
        print(f"――― Total Time: [{self._prof_timing_total:.2f}ms] ―――\n\n\n")

    def _set_pcall_obj(self, obj: Callable) -> ObjectCall:
        if not self._pcall_obj:
            self._pcall_obj = self._object_refs[obj]
            self._prof_timing_refs.update({self._pcall_obj: {}})
        return self._pcall_obj

    def _get_method_wrapper(
        self, method: Callable[P, RT]
    ) -> Union[Callable[P, RT], Callable[P, Awaitable[RT]]]:
        is_coroutine = inspect.iscoroutinefunction(method)
        timer_module = self._create_timer_module()
        if is_coroutine:
            return self._async_function_wrapper(method, timer_module)
        return self._function_wrapper(method, timer_module)

    def _class_wrapper(
        self, cls_obj: Type[Callable[P, CT]], timer_module: TimerModule
    ) -> Type[CT]:
        class ClassWrapper(cls_obj):  # type: ignore
            def __init__(_self, *args: P.args, **kwargs: P.kwargs) -> None:
                timer_module.start()
                super().__init__(*args, **kwargs)
                time_ms = timer_module.get_time_ms()
                timer_module.reset()
                pcall_obj = self._set_pcall_obj(cls_obj)
                self._append_object_profiling(pcall_obj, cls_obj, time_ms)

            def __new__(_cls: cls_obj, *args: P.args, **kwargs: P.kwargs) -> CT:
                self._set_pcall_obj(cls_obj)
                cls_instance = super().__new__(_cls)
                methods = inspect.getmembers(cls_instance, predicate=inspect.ismethod)
                for name, method in methods:
                    self._add_object_ref(method)
                    method = self._get_method_wrapper(method)
                    cls_instance = self._set_attribute(cls_instance, name, method)
                return cls_instance

        return ClassWrapper

    def _function_wrapper(
        self, func: Callable[P, RT], timer_module: TimerModule
    ) -> Callable[P, RT]:
        def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            pcall_obj = self._set_pcall_obj(func)
            timer_module.start()
            func_return = func(*args, **kwargs)
            time_ms = timer_module.get_time_ms()
            timer_module.reset()
            self._append_object_profiling(pcall_obj, func, time_ms)
            return func_return

        return function_wrapper

    def _async_function_wrapper(
        self, func: Callable[P, Awaitable[RT]], timer_module: TimerModule
    ) -> Callable[P, Awaitable[RT]]:
        async def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            pcall_obj = self._set_pcall_obj(func)
            timer_module.start()
            func_return = await func(*args, **kwargs)
            time_ms = timer_module.get_time_ms()
            timer_module.reset()
            self._append_object_profiling(pcall_obj, func, time_ms)
            return func_return

        return function_wrapper


class TimeProfiler(TimeProfilerBase):
    def class_profiler(self, c_obj: Type[Callable[P, CT]]) -> Type[CT]:
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
