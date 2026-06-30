"""
RPA for Python - Configuration and Constants
"""

import os
import platform

__version__ = '1.51.0'


class Config:
    """Configuration container for TagUI engine settings."""

    DEFAULT_TIMEOUT: float = 10.0
    DEFAULT_DELAY: float = 0.1

    def __init__(self) -> None:
        self._debug: bool = False
        self._error_mode: bool = False
        self._timeout: float = self.DEFAULT_TIMEOUT
        self._delay: float = self.DEFAULT_DELAY

        if platform.system() == 'Windows':
            self._tagui_location: str = os.environ['APPDATA']
        else:
            self._tagui_location: str = os.path.expanduser('~')

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

    @property
    def timeout(self) -> float:
        return self._timeout

    @timeout.setter
    def timeout(self, value: float) -> None:
        self._timeout = float(value)

    @property
    def delay(self) -> float:
        return self._delay

    @delay.setter
    def delay(self, value: float) -> None:
        self._delay = float(value)

    @property
    def tagui_location(self) -> str:
        return self._tagui_location

    @tagui_location.setter
    def tagui_location(self, location: str) -> None:
        self._tagui_location = location

    def get_tagui_directory(self) -> str:
        """Get the platform-specific TagUI directory path."""
        if platform.system() == 'Windows':
            return self._tagui_location + '/' + 'tagui'
        return self._tagui_location + '/' + '.tagui'

    def get_tagui_executable(self) -> str:
        """Get the path to the TagUI executable."""
        return self.get_tagui_directory() + '/' + 'src' + '/' + 'tagui'

    def get_end_processes_executable(self) -> str:
        """Get the path to the end_processes script."""
        return self.get_tagui_directory() + '/' + 'src' + '/' + 'end_processes'


TAGUI_LOCAL_JS = """\
// local custom helper function to check if UI element exists
// keep checking until timeout is reached before return result
// effect is interacting with element as soon as it appears

function exist(element_identifier) {

    var exist_timeout = Date.now() + casper.options.waitTimeout;

    while (Date.now() < exist_timeout) {
        if (present(element_identifier))
            return true;
        else
           sleep(100);
    }

    return false;

}

// function to replace add_concat() in tagui_header.js
// gain - echoing string with single and double quotes
// loss - no text-like variables usage since Python env

function add_concat(source_string) {

    return source_string;

}
"""