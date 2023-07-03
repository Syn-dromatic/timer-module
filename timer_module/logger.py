import logging
from typing import Union, Self

from logging import Logger, Formatter, StreamHandler
from logging import getLogger

from .metrics import CallableMetrics
from .terminal import YellowANSI, BlueANSI, RedANSI, ResetANSI


class LogHandlerBase:
    def __init__(self, name: str, level: Union[str, int]):
        self._name = name
        self._level = level
        self._logger = self._get_logger()
        self._handler = self._get_handler()
        self._formatter = self._get_formatter()
        self._setup()

    def _get_logger(self) -> Logger:
        logger = getLogger(self._name)
        logger.setLevel(self._level)
        return logger

    def _get_handler(self) -> StreamHandler:
        return StreamHandler()

    def _get_formatter(self) -> Formatter:
        log_format = "{}[%(name)s] [%(levelname)s] %(message)s{}"
        blue_code = BlueANSI().value
        reset_code = ResetANSI().value
        log_format = log_format.format(blue_code, reset_code)
        formatter = Formatter(log_format)
        return formatter

    def _setup(self):
        self._handler.setFormatter(self._formatter)
        self._logger.addHandler(self._handler)


class LogHandler(LogHandlerBase):
    def __init__(self, name: str, level: Union[str, int]):
        if not hasattr(self, "initialized"):
            super().__init__(name, level)
            self.initialized = True

    def __new__(cls, *args, **kwargs) -> Self:
        if not hasattr(cls, "instance") or not isinstance(cls.instance, cls):
            cls.instance = super(LogHandler, cls).__new__(cls)
        return cls.instance

    def log_debug(self, reference: str, message: str):
        yellow_code = YellowANSI().value
        string = f"[{reference}]: {yellow_code}[{message}]"
        self._logger.debug(string)

    def log_info(self, reference: str, message: str):
        yellow_code = YellowANSI().value
        string = f"[{reference}]: {yellow_code}[{message}]"
        self._logger.info(string)

    def log_warning(self, reference: str, message: str):
        yellow_code = YellowANSI().value
        string = f"[{reference}]: {yellow_code}[{message}]"
        self._logger.warning(string)

    def log_error(self, reference: str, message: str):
        red_code = RedANSI().value
        string = f"[{reference}]: {red_code}[{message}]"
        self._logger.error(string)

    def log_critical(self, reference: str, message: str):
        red_code = RedANSI().value
        string = f"[{reference}]: {red_code}[{message}]"
        self._logger.critical(string)


class TimeProfilerLogger:
    def __init__(self):
        self.log_handler: LogHandler = LogHandler("TimeProfiler", logging.DEBUG)

    def add_call_reference(self, call_metrics: CallableMetrics):
        call_identifier = call_metrics.get_call_identifier()
        call_hash = call_metrics.call_hash
        reference = "AddCallReference"
        message = f"CallIdentifier:{call_identifier} ║ Hash:{call_hash}"
        self.log_handler.log_debug(reference, message)

    def set_primary_call(self, call_metrics: CallableMetrics):
        call_identifier = call_metrics.get_call_identifier()
        call_hash = call_metrics.call_hash
        reference = "SetPrimaryCall"
        message = f"CallIdentifier:{call_identifier} ║ Hash:{call_hash}"
        self.log_handler.log_debug(reference, message)

    def subcall_event(self, call_metrics: CallableMetrics):
        call_identifier = call_metrics.get_call_identifier()
        call_hash = call_metrics.call_hash
        reference = "SubCallEvent"
        message = f"CallIdentifier:{call_identifier} ║ Hash:{call_hash}"
        self.log_handler.log_debug(reference, message)
