import time


class TimerModule:
    __slots__ = ["is_running", "st_time", "cr_time"]

    def __init__(self) -> None:
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
