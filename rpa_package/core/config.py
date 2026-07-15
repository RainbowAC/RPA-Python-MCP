"""Configuration and constants for desktop automation runtime."""

__version__ = '1.51.1'


class Config:
    """Configuration container for desktop engine settings."""

    def __init__(self) -> None:
        self._debug: bool = False
        self._error_mode: bool = False

    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, value: bool) -> None:
        self._debug = value

    @property
    def error_mode(self) -> bool:
        return self._error_mode

    @error_mode.setter
    def error_mode(self, value: bool) -> None:
        self._error_mode = value