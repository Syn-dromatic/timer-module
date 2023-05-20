import hashlib

from time import perf_counter_ns

from typing import Callable, Awaitable
from typing import Union, Optional, Type, TypeVar, ParamSpec
from inspect import getmembers, ismethod, isfunction, iscoroutinefunction

from .converters import TimeFormatter
from .stdio import Stdio
from .stdio import ANSICode, GreenANSI, YellowANSI, WhiteANSI, CyanANSI


P = ParamSpec("P")
RT = TypeVar("RT")
CT = TypeVar("CT")


class ObjectCall:
    __slots__ = ("name", "module", "time_ns", "ncalls")

    def __init__(self, name: str, module: str, time: float, ncalls: int):
        self.name = name
        self.module = module
        self.time_ns = time
        self.ncalls = ncalls

    def get_percall_time(self) -> float:
        if self.ncalls > 0:
            percall_time_ns = self.time_ns / self.ncalls
            return percall_time_ns
        return 0.0


class ProfileReport:
    def __init__(self, realtime: bool = False):
        self.stdio = Stdio()
        self.realtime = realtime
        self.header_color = self.get_header_color()
        self.call_color = self.get_call_color()
        self.total_color = CyanANSI()

    def get_header_color(self) -> ANSICode:
        if self.realtime:
            return YellowANSI()
        return GreenANSI()

    def get_call_color(self) -> ANSICode:
        if self.realtime:
            return CyanANSI()
        return WhiteANSI()

    def get_relative_percentage(self, pcall_ns: float, obj_ns: float) -> float:
        percentage = 0.0
        if pcall_ns > 0.0 and obj_ns > 0.0:
            percentage = (obj_ns / pcall_ns) * 100
        return percentage

    def print_primary_call_header(self, object_call: ObjectCall):
        pcall_name = object_call.name
        profile_header = "█ PROFILE: {} █"
        profile_header = profile_header.format(pcall_name)
        separator = "=" * len(profile_header)
        string = "\n{}\n{}"
        string = string.format(profile_header, separator)
        self.stdio.set_ansi_color(self.header_color)
        self.stdio.stdout(string)

    def print_primary_call(self, primary_call: ObjectCall):
        pcall_time_ns = primary_call.time_ns
        pcall_ncalls = primary_call.ncalls
        percall_time_ns = primary_call.get_percall_time()

        pcall_time = TimeFormatter(pcall_time_ns).auto_format_time()
        percall_time = TimeFormatter(percall_time_ns).auto_format_time()
        string = "Profile Time: [{}]\nNCalls: [{}] — PerCall: [{}]\n——————\n"
        string = string.format(pcall_time, pcall_ncalls, percall_time)
        self.stdio.set_ansi_color(self.call_color)
        self.stdio.stdout(string)

    def print_call(self, object_call: ObjectCall, pcall_time: float):
        obj_name = object_call.name
        obj_time_ns = object_call.time_ns
        obj_ncalls = object_call.ncalls
        percall_time_ns = object_call.get_percall_time()

        prc = self.get_relative_percentage(pcall_time, obj_time_ns)
        obj_time = TimeFormatter(obj_time_ns).auto_format_time()
        percall_time = TimeFormatter(percall_time_ns).auto_format_time()

        string = "Name: {}\nTime: [{}] — T%: {:.2f}%\nNCalls: [{}] — PerCall: [{}]\n——"
        string = string.format(obj_name, obj_time, prc, obj_ncalls, percall_time)
        self.stdio.set_ansi_color(self.call_color)
        self.stdio.stdout(string)

    def print_profiling_report(
        self,
        object_refs: dict[int, ObjectCall],
        timing_refs: dict[int, set[int]],
        total_time_ns: float,
    ):
        for pcall_hash, ref_list in timing_refs.items():
            pcall_object = object_refs[pcall_hash]
            self.print_primary_call_header(pcall_object)
            pcall_time = pcall_object.time_ns
            for ref_hash in ref_list:
                if ref_hash == pcall_hash:
                    continue
                object_call = object_refs[ref_hash]
                self.print_call(object_call, pcall_time)

            self.print_primary_call(pcall_object)

        total_time = TimeFormatter(total_time_ns).auto_format_time()
        string = "――― Total Time: [{}] ―――\n\n\n"
        string = string.format(f"{total_time}")
        self.stdio.set_ansi_color(self.total_color)
        self.stdio.stdout(string)


class TimeProfilerBase:
    def __init__(self, realtime: bool = False) -> None:
        self._realtime: bool = realtime

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance") or not isinstance(cls.instance, cls):
            cls.instance = super(TimeProfilerBase, cls).__new__(cls)
            cls._object_refs: dict[int, ObjectCall] = {}
            cls._timing_refs: dict[int, set[int]] = {}
            cls._timing_total: float = 0.0
            cls._pcall_hash: Optional[int] = None
        return cls.instance

    def __del__(self) -> None:
        self._print_report()

    def _print_report(self, realtime: bool = False):
        report = ProfileReport(realtime)
        object_refs = self._object_refs
        timing_refs = self._timing_refs
        total_time = self._timing_total
        report.print_profiling_report(object_refs, timing_refs, total_time)

    @staticmethod
    def _set_attribute(instance: CT, name: str, method: Callable) -> CT:
        try:
            instance.__setattr__(name, method)
        except AttributeError:
            print(f"Class Method ({name}) is read-only and cannot be timed.")
        return instance

    def _append_object_profiling(self, object_hash: int, time_ns: float) -> None:
        object_refs = self._object_refs
        pcall_obj = self._pcall_hash

        object_call = object_refs[object_hash]
        object_call.time_ns += time_ns
        object_call.ncalls += 1

        if pcall_obj is not None:
            if object_hash == pcall_obj:
                self._timing_total += time_ns
                self._pcall_hash = None

                if self._realtime:
                    self._print_report(realtime=True)

    @staticmethod
    def _create_object_call(obj: Callable) -> ObjectCall:
        obj_name = obj.__qualname__
        obj_module = obj.__module__

        obj_call = ObjectCall(
            name=obj_name,
            module=obj_module,
            time=0.0,
            ncalls=0,
        )
        return obj_call

    @staticmethod
    def hash_type_id(type_id: Type) -> int:
        hasher = hashlib.sha1()
        hasher.update(str(type_id).encode())
        hash_result = int(hasher.hexdigest(), 16)
        return hash_result

    def _set_pcall_hash(self, object_hash: int) -> int:
        pcall_hash = self._pcall_hash

        if pcall_hash is None:
            pcall_hash = object_hash
            self._pcall_hash = pcall_hash
            self._timing_refs[pcall_hash] = set()

        pcall_timing = self._timing_refs[pcall_hash]
        pcall_timing.add(object_hash)

        return object_hash

    def _add_object_ref(self, obj: Callable) -> int:
        hash_ref = self.hash_type_id(obj)
        object_call = self._create_object_call(obj)
        self._object_refs[hash_ref] = object_call
        return hash_ref

    def _get_method_wrapper(
        self, method: Callable[P, RT], main_ref: int
    ) -> Union[Callable[P, RT], Callable[P, Awaitable[RT]]]:
        is_coroutine = iscoroutinefunction(method)
        if is_coroutine:
            return self._async_function_wrapper(method, main_ref)
        return self._function_wrapper(method, main_ref)

    def _class_wrapper(self, cls_obj: Type[Callable[P, CT]], main_ref: int) -> Type[CT]:
        class ClassWrapper(cls_obj):  # type: ignore
            def __init__(_self, *args: P.args, **kwargs: P.kwargs) -> None:
                hash_ref = self._set_pcall_hash(main_ref)
                start_time = perf_counter_ns()
                super().__init__(*args, **kwargs)
                elapsed_time = perf_counter_ns() - start_time
                self._append_object_profiling(hash_ref, elapsed_time)

            def __new__(_cls: cls_obj, *args: P.args, **kwargs: P.kwargs) -> CT:
                cls_instance = super().__new__(_cls)
                methods = getmembers(cls_instance, predicate=ismethod)
                functions = getmembers(cls_instance, predicate=isfunction)
                members = methods + functions
                for name, member in members:
                    member_ref = self._add_object_ref(member)
                    member = self._get_method_wrapper(member, member_ref)
                    cls_instance = self._set_attribute(cls_instance, name, member)

                return cls_instance

        return ClassWrapper

    def _function_wrapper(
        self, func: Callable[P, RT], main_ref: int
    ) -> Callable[P, RT]:
        def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            hash_ref = self._set_pcall_hash(main_ref)
            start_time = perf_counter_ns()
            result = func(*args, **kwargs)
            elapsed_time = perf_counter_ns() - start_time
            self._append_object_profiling(hash_ref, elapsed_time)
            return result

        return function_wrapper

    def _async_function_wrapper(
        self, func: Callable[P, Awaitable[RT]], main_ref: int
    ) -> Callable[P, Awaitable[RT]]:
        async def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            hash_ref = self._set_pcall_hash(main_ref)
            start_time = perf_counter_ns()
            result = await func(*args, **kwargs)
            elapsed_time = perf_counter_ns() - start_time
            self._append_object_profiling(hash_ref, elapsed_time)
            return result

        return function_wrapper


class TimeProfiler(TimeProfilerBase):
    def class_profiler(self, cls_obj: Type[Callable[P, CT]]) -> Type[CT]:
        main_ref = self._add_object_ref(cls_obj)
        return self._class_wrapper(cls_obj, main_ref)

    def function_profiler(self, func: Callable[P, RT]) -> Callable[P, RT]:
        main_ref = self._add_object_ref(func)
        return self._function_wrapper(func, main_ref)

    def async_function_profiler(
        self, func: Callable[P, Awaitable[RT]]
    ) -> Callable[P, Awaitable[RT]]:
        main_ref = self._add_object_ref(func)
        return self._async_function_wrapper(func, main_ref)
