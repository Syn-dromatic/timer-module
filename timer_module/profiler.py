import hashlib

from time import time_ns

from typing import Callable, Awaitable
from typing import Union, Optional, Type, TypeVar, ParamSpec

from inspect import getmembers, ismethod, isfunction, iscoroutinefunction


P = ParamSpec("P")
RT = TypeVar("RT")
CT = TypeVar("CT")


class ObjectCall:
    __slots__ = ("name", "module", "time", "ncalls")

    def __init__(self, name: str, module: str, time: float, ncalls: int):
        self.name = name
        self.module = module
        self.time = time
        self.ncalls = ncalls


class TimeProfilerBase:
    def __init__(self, realtime: bool = False) -> None:
        self._realtime: bool = realtime

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance") or not isinstance(cls.instance, cls):
            cls.instance = super(TimeProfilerBase, cls).__new__(cls)
            cls._prof_timing_refs: dict[int, set[int]] = {}
            cls._prof_timing_total: float = 0.0
            cls._object_refs: dict[int, ObjectCall] = {}
            cls._pcall_hash: Optional[int] = None
        return cls.instance

    def __del__(self) -> None:
        report_str = "END REPORT"
        print(f"{'=' * len(report_str)}\n{report_str}\n{'=' * len(report_str)}\n")
        self._print_profiling_report()

    @staticmethod
    def _set_attribute(instance: CT, name: str, method: Callable) -> CT:
        try:
            instance.__setattr__(name, method)
        except AttributeError:
            print(f"Class Method ({name}) is read-only and cannot be timed.")
        return instance

    def _append_object_profiling(self, object_hash: int, duration: float) -> None:
        object_refs = self._object_refs
        pcall_obj = self._pcall_hash

        object_call = object_refs[object_hash]
        object_call.time += duration
        object_call.ncalls += 1

        if pcall_obj is not None:
            if object_hash == pcall_obj:
                self._prof_timing_total += duration
                self._pcall_hash = None

                if self._realtime:
                    self._print_profiling_report()

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

    @staticmethod
    def _print_pcall_header(object_call: ObjectCall) -> None:
        pcall_name = object_call.name
        profile_header = f"█ PROFILE: {pcall_name} █"
        header_len = len(profile_header)
        header = "=" * header_len
        print(f"\n{profile_header}\n{header}")

    def _print_pcall(self, object_call: ObjectCall) -> None:
        pcall_time = object_call.time
        pcall_ncalls = object_call.ncalls
        pcall_percall = pcall_time / pcall_ncalls

        f_pcall_time = self._format_time(pcall_time)
        f_pcall_percall = self._format_time(pcall_percall)

        print(
            "Profile Time: [{}]\nNCalls: [{}] — PerCall: [{}]\n——————\n".format(
                f_pcall_time, pcall_ncalls, f_pcall_percall
            )
        )

    def _print_call(self, object_call: ObjectCall, pcall_time: float) -> None:
        obj_name = object_call.name
        obj_time = object_call.time

        obj_ncalls = object_call.ncalls
        obj_percall = obj_time / obj_ncalls

        f_obj_time = self._format_time(obj_time)
        f_obj_percall = self._format_time(obj_percall)

        t_prc = 0
        if obj_time != 0 and pcall_time != 0:
            t_prc = (obj_time / pcall_time) * 100

        print(
            "Name: {}\nTime: [{}] — T%: {:.2f}%\nNCalls: [{}] — PerCall: [{}]\n——".format(
                obj_name, f_obj_time, t_prc, obj_ncalls, f_obj_percall
            )
        )

    def _print_profiling_report(self) -> None:
        object_refs = self._object_refs

        for pcall_hash, obj_list in self._prof_timing_refs.items():
            pcall_object = object_refs[pcall_hash]
            self._print_pcall_header(pcall_object)
            pcall_time = pcall_object.time
            for object_hash in obj_list:
                if object_hash == pcall_hash:
                    continue
                object_call = object_refs[object_hash]
                self._print_call(object_call, pcall_time)

            self._print_pcall(pcall_object)

        time_total = self._format_time(self._prof_timing_total)
        print("――― Total Time: [{}] ―――\n\n\n".format(f"{time_total}"))

    def _set_pcall_hash(self, object_hash: int) -> int:
        pcall_hash = self._pcall_hash

        if pcall_hash is None:
            pcall_hash = object_hash
            self._pcall_hash = pcall_hash
            self._prof_timing_refs[pcall_hash] = set()

        pcall_timing = self._prof_timing_refs[pcall_hash]
        pcall_timing.add(object_hash)

        return object_hash

    def _add_object_ref(self, obj: Callable) -> int:
        hash_ref = self.hash_type_id(obj)
        object_call = self._create_object_call(obj)
        self._object_refs[hash_ref] = object_call
        return hash_ref

    @staticmethod
    def _format_time(nanos: float) -> str:
        if nanos >= 1e9:
            secs = nanos / 1e9
            return f"{secs:.2f}s"

        elif nanos >= 1e6:
            millis = nanos / 1e6
            return f"{millis:.2f}ms"

        elif nanos >= 1e3:
            micros = nanos / 1e3
            return f"{micros:.2f}μs"

        else:
            return f"{nanos:.2f}ns"

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
                start_time = time_ns()
                super().__init__(*args, **kwargs)
                elapsed_time = time_ns() - start_time
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
            start_time = time_ns()
            result = func(*args, **kwargs)
            elapsed_time = time_ns() - start_time
            self._append_object_profiling(hash_ref, elapsed_time)
            return result

        return function_wrapper

    def _async_function_wrapper(
        self, func: Callable[P, Awaitable[RT]], main_ref: int
    ) -> Callable[P, Awaitable[RT]]:
        async def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            hash_ref = self._set_pcall_hash(main_ref)
            start_time = time_ns()
            result = await func(*args, **kwargs)
            elapsed_time = time_ns() - start_time
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
