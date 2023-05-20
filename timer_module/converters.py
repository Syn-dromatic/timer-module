class TimeFormatter:
    def __init__(self, nanos: float):
        self.nanos = nanos

    def auto_format_time(self) -> str:
        nanos = self.nanos
        if nanos >= 1e9:
            secs = nanos / 1e9
            return f"{secs:.2f}s"

        elif nanos >= 1e6:
            millis = nanos / 1e6
            return f"{millis:.2f}ms"

        elif nanos >= 1e3:
            micros = nanos / 1e3
            return f"{micros:.2f}μs"

        return f"{nanos:.2f}ns"

