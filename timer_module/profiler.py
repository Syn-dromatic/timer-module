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

    def __post_init__(self) -> None:
        self.refname: str = f"{self.module}.{self.name}"
        self.hash: int = hash(self.refname)

    def __hash__(self) -> int:
        return self.hash

    def __eq__(self, __o: object) -> bool:
        return __o.__hash__() == self.hash

    def __ne__(self, __o: object) -> bool:
        return not __o.__hash__() == self.hash


class TimeProfilerBase:
    def __init__(self, realtime: bool = False) -> None:
        self._realtime: bool = realtime

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance") or not isinstance(cls.instance, cls):
            cls.instance = super(TimeProfilerBase, cls).__new__(cls)
            cls._prof_timing_refs: dict[ObjectCall, dict[Callable, ObjectCall]] = {}
            cls._prof_timing_total: float = 0
            cls._object_refs: dict[Callable, ObjectCall] = {}
            cls._pcall_obj: Optional[ObjectCall] = None
        return cls.instance

    def __del__(self) -> None:
        report_str = "END REPORT"
        print(f"{'=' * len(report_str)}\n{report_str}\n{'=' * len(report_str)}\n")
        self._profiling_report()

    @staticmethod
    def _create_object_call(obj: Callable) -> ObjectCall:
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

    def _add_object_ref(self, obj: Callable) -> None:
        obj_call = self._create_object_call(obj)
        if obj_call not in self._object_refs:
            self._object_refs.update({obj: obj_call})

    def _append_object_profiling(self, obj_call: ObjectCall, time_ms: float) -> None:
        obj_call.time += time_ms
        obj_call.ncalls += 1
        if obj_call == self._pcall_obj:
            self._prof_timing_total += time_ms
            self._pcall_obj = None

            if self._realtime:
                self._profiling_report()

    @staticmethod
    def _format_time(time: float) -> str:
        if time >= 0.01:
            return f"{time:.2f}ms"
        return f"{time*1000000:.2f}ns"

    @staticmethod
    def _print_pcall_header(obj_call: ObjectCall) -> None:
        pcall_name = obj_call.name
        profile_header = f"█ PROFILE: {pcall_name} █"
        header_len = len(profile_header)
        print(f"\n{profile_header}\n" f"{'=' * header_len}")

    def _print_pcall(self, obj_call: ObjectCall) -> None:
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

    def _print_call(self, obj_call: ObjectCall, pcall_time: float) -> None:
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

    def _profiling_report(self) -> None:
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
        obj_call = self._object_refs[obj]
        if not self._pcall_obj:
            self._pcall_obj = obj_call
            self._prof_timing_refs[obj_call] = {}
        self._prof_timing_refs[self._pcall_obj][obj] = obj_call
        return obj_call

    def _get_method_wrapper(
        self, method: Callable[P, RT]
    ) -> Union[Callable[P, RT], Callable[P, Awaitable[RT]]]:
        is_coroutine = inspect.iscoroutinefunction(method)
        if is_coroutine:
            return self._async_function_wrapper(method)
        return self._function_wrapper(method)

    def _class_wrapper(self, cls_obj: Type[Callable[P, CT]]) -> Type[CT]:
        class ClassWrapper(cls_obj):  # type: ignore
            def __init__(_self, *args: P.args, **kwargs: P.kwargs) -> None:
                obj_call = self._set_pcall_obj(cls_obj)
                st_timestamp = time.time_ns() / 1_000_000
                super().__init__(*args, **kwargs)
                time_ms = (time.time_ns() / 1_000_000) - st_timestamp
                self._append_object_profiling(obj_call, time_ms)

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

    def _function_wrapper(self, func: Callable[P, RT]) -> Callable[P, RT]:
        def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            obj_call = self._set_pcall_obj(func)
            st_timestamp = time.time_ns() / 1_000_000
            func_return = func(*args, **kwargs)
            time_ms = (time.time_ns() / 1_000_000) - st_timestamp
            self._append_object_profiling(obj_call, time_ms)
            return func_return

        return function_wrapper

    def _async_function_wrapper(
        self, func: Callable[P, Awaitable[RT]]
    ) -> Callable[P, Awaitable[RT]]:
        async def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            obj_call = self._set_pcall_obj(func)
            st_timestamp = time.time_ns() / 1_000_000
            func_return = await func(*args, **kwargs)
            time_ms = (time.time_ns() / 1_000_000) - st_timestamp
            self._append_object_profiling(obj_call, time_ms)
            return func_return

        return function_wrapper


class TimeProfiler(TimeProfilerBase):
    def class_profiler(self, cls_obj: Type[Callable[P, CT]]) -> Type[CT]:
        self._add_object_ref(cls_obj)
        return self._class_wrapper(cls_obj)

    def function_profiler(self, func: Callable[P, RT]) -> Callable[P, RT]:
        self._add_object_ref(func)
        return self._function_wrapper(func)

    def async_function_profiler(
        self, func: Callable[P, Awaitable[RT]]
    ) -> Callable[P, Awaitable[RT]]:
        self._add_object_ref(func)
        return self._async_function_wrapper(func)
