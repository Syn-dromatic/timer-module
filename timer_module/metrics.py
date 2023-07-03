from copy import copy

from .hasher import Hasher
from .terminal import Terminal
from .terminal import ANSICode, GreenANSI, YellowANSI, WhiteANSI, CyanANSI


class TimeFormatterNs:
    def __init__(self, nanos: float):
        self.nanos = nanos

    def format_seconds(self) -> str:
        secs = self.nanos / 1e9
        return f"{secs:.2f}s"

    def format_milliseconds(self) -> str:
        millis = self.nanos / 1e6
        return f"{millis:.2f}ms"

    def format_microseconds(self) -> str:
        micros = self.nanos / 1e3
        return f"{micros:.2f}μs"

    def format_nanoseconds(self) -> str:
        return f"{self.nanos:.2f}ns"

    def auto_format(self) -> str:
        nanos = self.nanos
        if nanos >= 1e9:
            return self.format_seconds()

        elif nanos >= 1e6:
            return self.format_milliseconds()

        elif nanos >= 1e3:
            return self.format_microseconds()

        return self.format_nanoseconds()


class CallableMetrics:
    __slots__ = ("name", "module", "suffix", "call_hash", "ncalls", "time_ns")

    def __init__(
        self,
        name: str,
        module: str,
        suffix: str,
        ncalls: int,
        time_ns: float,
    ):
        self.name = name
        self.module = module
        self.suffix = suffix
        self.ncalls = ncalls
        self.time_ns = time_ns
        self.call_hash = self.get_hash()

    def __hash__(self) -> int:
        return self.call_hash

    def get_hash(self) -> int:
        call_identifier = self.get_call_identifier()
        return Hasher(call_identifier).hash_sha1()

    def get_call_identifier(self) -> str:
        call_identifier = f"{self.module}.{self.name}"
        return call_identifier

    def get_percall_time(self) -> float:
        if self.ncalls > 0:
            percall_time_ns = self.time_ns / self.ncalls
            return percall_time_ns
        return 0.0

    def fresh_copy(self) -> "CallableMetrics":
        call_metrics = copy(self)
        call_metrics.ncalls = 0
        call_metrics.time_ns = 0.0
        return call_metrics


class ProfileMetricsReport:
    def __init__(self, realtime: bool = False):
        self.realtime = realtime
        self.terminal = Terminal()
        self.header_color = self.get_header_color()
        self.call_color = self.get_call_color()
        self.total_time_color = self.get_total_time_color()

    def get_header_color(self) -> ANSICode:
        if self.realtime:
            return YellowANSI()
        return GreenANSI()

    def get_call_color(self) -> ANSICode:
        if self.realtime:
            return CyanANSI()
        return WhiteANSI()

    def get_total_time_color(self) -> ANSICode:
        if self.realtime:
            return YellowANSI()
        return GreenANSI()

    def get_relative_percentage(self, pcall_ns: float, call_ns: float) -> float:
        percentage = 0.0
        if pcall_ns > 0.0 and call_ns > 0.0:
            percentage = (call_ns / pcall_ns) * 100
        return percentage

    def write_primary_call_header(self, call_metrics: CallableMetrics):
        pcall_name = call_metrics.name
        pcall_suffix = call_metrics.suffix
        if pcall_suffix:
            pcall_name += f" ({pcall_suffix})"

        profile_header = "█ PROFILE: {} █"
        profile_header = profile_header.format(pcall_name)
        separator = "=" * len(profile_header)
        string = "\n{}\n{}"
        string = string.format(profile_header, separator)
        self.terminal.set_ansi_color(self.header_color)
        self.terminal.write(string)

    def write_primary_call_report(self, pcall_metrics: CallableMetrics):
        pcall_time_ns = pcall_metrics.time_ns
        pcall_ncalls = pcall_metrics.ncalls
        percall_time_ns = pcall_metrics.get_percall_time()

        pcall_time = TimeFormatterNs(pcall_time_ns).auto_format()
        percall_time = TimeFormatterNs(percall_time_ns).auto_format()
        string = "Profile Time: [{}]\nNCalls: [{}] — PerCall: [{}]\n——————\n"
        string = string.format(pcall_time, pcall_ncalls, percall_time)
        self.terminal.set_ansi_color(self.call_color)
        self.terminal.write(string)

    def write_call_report(self, call_metrics: CallableMetrics, pcall_time: float):
        call_name = call_metrics.name
        call_suffix = call_metrics.suffix
        if call_suffix:
            call_name += f" ({call_suffix})"
        call_time_ns = call_metrics.time_ns
        call_ncalls = call_metrics.ncalls
        percall_time_ns = call_metrics.get_percall_time()

        prc = self.get_relative_percentage(pcall_time, call_time_ns)
        call_time = TimeFormatterNs(call_time_ns).auto_format()
        percall_time = TimeFormatterNs(percall_time_ns).auto_format()

        string = "Name: {}\nTime: [{}] — T%: {:.2f}%\nNCalls: [{}] — PerCall: [{}]\n——"
        string = string.format(call_name, call_time, prc, call_ncalls, percall_time)
        self.terminal.set_ansi_color(self.call_color)
        self.terminal.write(string)

    def get_total_time(
        self,
        callable_refs: dict[int, CallableMetrics],
        timing_refs: dict[int, dict[int, CallableMetrics]],
    ):
        total_time = 0.0
        for pcall_hash, _ in timing_refs.items():
            total_time += callable_refs[pcall_hash].time_ns
        return total_time

    def write_report(
        self,
        callable_refs: dict[int, CallableMetrics],
        timing_refs: dict[int, dict[int, CallableMetrics]],
    ):
        for pcall_hash, subcalls in timing_refs.items():
            pcall_metrics = callable_refs[pcall_hash]
            self.write_primary_call_header(pcall_metrics)
            pcall_time = pcall_metrics.time_ns
            for _, subcall_metrics in subcalls.items():
                if subcall_metrics == pcall_metrics:
                    continue
                self.write_call_report(subcall_metrics, pcall_time)
            self.write_primary_call_report(pcall_metrics)

        total_time_ns = self.get_total_time(callable_refs, timing_refs)
        total_time = TimeFormatterNs(total_time_ns).auto_format()

        string = "――― Total Time: [{}] ―――\n\n\n"
        string = string.format(f"{total_time}")
        self.terminal.set_ansi_color(self.total_time_color)
        self.terminal.write(string)
