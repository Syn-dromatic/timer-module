from time import perf_counter_ns
from typing import Callable, Awaitable, Self
from typing import Union, Optional, Type, TypeVar, ParamSpec
from inspect import getmembers, ismethod, isfunction, iscoroutinefunction

from .metrics import CallableMetrics, ProfileMetricsReport
from .logger import TimeProfilerLogger

P = ParamSpec("P")
RT = TypeVar("RT")
CT = TypeVar("CT")


class TimeProfilerBase:
    def __init__(self, realtime: bool = False, verbose: bool = False) -> None:
        self._realtime: bool = realtime
        self._verbose: bool = verbose
        self._profiler_logger: TimeProfilerLogger = TimeProfilerLogger()

    def __new__(cls, *args, **kwargs) -> Self:
        if not hasattr(cls, "instance") or not isinstance(cls.instance, cls):
            cls.instance = super(TimeProfilerBase, cls).__new__(cls)
            cls._callable_refs: dict[int, CallableMetrics] = {}
            cls._timing_refs: dict[int, dict[int, CallableMetrics]] = {}
            cls._pcall_hash: Optional[int] = None
        return cls.instance

    def __del__(self) -> None:
        self._print_report()

    def _print_report(self, realtime: bool = False):
        metrics_report = ProfileMetricsReport(realtime)
        callable_refs = self._callable_refs
        timing_refs = self._timing_refs
        metrics_report.write_report(callable_refs, timing_refs)

    @staticmethod
    def _set_attribute(instance: CT, name: str, method: Callable) -> CT:
        try:
            instance.__setattr__(name, method)
        except AttributeError:
            print(f"Class Method ({name}) is read-only and cannot be timed.")
        return instance

    def _append_metrics(self, call_hash: int, time_ns: float) -> None:
        pcall_hash = self._pcall_hash

        if pcall_hash is not None:
            if call_hash == pcall_hash:
                call_metrics = self._callable_refs[call_hash]
                call_metrics.time_ns += time_ns
                call_metrics.ncalls += 1
                self._pcall_hash = None

                if self._realtime:
                    self._print_report(realtime=True)
            else:
                call_metrics = self._timing_refs[pcall_hash][call_hash]
                call_metrics.time_ns += time_ns
                call_metrics.ncalls += 1
                if self._verbose:
                    self._profiler_logger.subcall_event(call_metrics)

    @staticmethod
    def _create_callable_metrics(call: Callable, suffix: str) -> CallableMetrics:
        name = call.__qualname__
        module = call.__module__

        call_metrics = CallableMetrics(
            name=name,
            module=module,
            suffix=suffix,
            ncalls=0,
            time_ns=0.0,
        )
        return call_metrics

    def _set_pcall_hash(self, call_hash: int):
        pcall_hash = self._pcall_hash

        if pcall_hash is None:
            pcall_hash = call_hash
            self._pcall_hash = pcall_hash
            if pcall_hash not in self._timing_refs:
                self._timing_refs[pcall_hash] = {}

            call_metrics = self._callable_refs[pcall_hash]
            if self._verbose:
                self._profiler_logger.set_primary_call(call_metrics)
            return

        pcall_timing = self._timing_refs[pcall_hash]
        if call_hash not in pcall_timing:
            call_metrics = self._callable_refs[call_hash]
            new_metrics = call_metrics.fresh_copy()
            pcall_timing.update({call_hash: new_metrics})

    def _add_call_ref(self, call: Callable, suffix: str = "") -> int:
        call_metrics = self._create_callable_metrics(call, suffix)
        call_hash = call_metrics.call_hash
        self._callable_refs[call_hash] = call_metrics
        if self._verbose:
            self._profiler_logger.add_call_reference(call_metrics)
        return call_hash

    def _get_method_wrapper(
        self, method: Callable[P, RT], method_hash: int
    ) -> Union[Callable[P, RT], Callable[P, Awaitable[RT]]]:
        is_coroutine = iscoroutinefunction(method)
        if is_coroutine:
            return self._async_function_wrapper(method, method_hash)
        return self._function_wrapper(method, method_hash)

    def _class_wrapper(
        self, cls_obj: Type[Callable[P, CT]], pcall_hash: int
    ) -> Type[CT]:
        class ClassWrapper(cls_obj):  # type: ignore
            def __init__(_self, *args: P.args, **kwargs: P.kwargs) -> None:
                self._set_pcall_hash(pcall_hash)
                start_time = perf_counter_ns()
                super().__init__(*args, **kwargs)
                elapsed_time = perf_counter_ns() - start_time
                self._append_metrics(pcall_hash, elapsed_time)

            def __new__(_cls: cls_obj, *args: P.args, **kwargs: P.kwargs) -> CT:
                cls_instance = super().__new__(_cls)
                methods = getmembers(cls_instance, predicate=ismethod)
                functions = getmembers(cls_instance, predicate=isfunction)
                members = methods + functions
                for name, member in members:
                    if member.__module__ != __name__:
                        member_ref = self._add_call_ref(member)
                        member = self._get_method_wrapper(member, member_ref)
                        cls_instance = self._set_attribute(cls_instance, name, member)

                return cls_instance

        return ClassWrapper

    def _function_wrapper(
        self, func: Callable[P, RT], pcall_hash: int
    ) -> Callable[P, RT]:
        def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            self._set_pcall_hash(pcall_hash)
            start_time = perf_counter_ns()
            result = func(*args, **kwargs)
            elapsed_time = perf_counter_ns() - start_time
            self._append_metrics(pcall_hash, elapsed_time)
            return result

        return function_wrapper

    def _async_function_wrapper(
        self, func: Callable[P, Awaitable[RT]], pcall_hash: int
    ) -> Callable[P, Awaitable[RT]]:
        async def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            self._set_pcall_hash(pcall_hash)
            start_time = perf_counter_ns()
            result = await func(*args, **kwargs)
            elapsed_time = perf_counter_ns() - start_time
            self._append_metrics(pcall_hash, elapsed_time)
            return result

        return function_wrapper


class TimeProfiler(TimeProfilerBase):
    def class_profiler(self, cls_obj: Type[Callable[P, CT]]) -> Type[CT]:
        main_ref = self._add_call_ref(cls_obj, "Initialization")
        return self._class_wrapper(cls_obj, main_ref)

    def function_profiler(self, func: Callable[P, RT]) -> Callable[P, RT]:
        main_ref = self._add_call_ref(func)
        return self._function_wrapper(func, main_ref)

    def async_function_profiler(
        self, func: Callable[P, Awaitable[RT]]
    ) -> Callable[P, Awaitable[RT]]:
        main_ref = self._add_call_ref(func)
        return self._async_function_wrapper(func, main_ref)
