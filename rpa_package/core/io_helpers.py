"""
RPA for Python - I/O Helper Functions
"""

import os
import time
from typing import IO, Optional


class IOHelper:
    """Helper class for file I/O operations."""

    def __init__(self, delay: float = 0.1) -> None:
        self._delay: float = delay

    @staticmethod
    def open_file(filename: str, mode: str = 'r') -> IO:
        """Open a file with UTF-8 encoding."""
        return open(filename, mode, encoding='utf-8')

    @staticmethod
    def load_file(filename: str) -> str:
        """Load and return the contents of a file."""
        if not os.path.isfile(filename):
            raise FileNotFoundError(f'Cannot load file {filename}')
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def dump_file(text: str, filename: str) -> None:
        """Write text to a file, overwriting existing content."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)

    @staticmethod
    def append_file(text: str, filename: str) -> None:
        """Append text to a file."""
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(text)

    @staticmethod
    def safe_remove(filename: str) -> None:
        """Safely remove a file if it exists."""
        if os.path.isfile(filename):
            os.remove(filename)

    def wait_for_output_file(self, filename: str, fallback_filename: Optional[str] = None) -> str:
        """Wait for an output file to appear, read it, and delete it."""
        while not os.path.isfile(filename):
            if fallback_filename and os.path.isfile(fallback_filename):
                break
            time.sleep(self._delay)

        if os.path.isfile(filename):
            text = self.load_file(filename)
            self.safe_remove(filename)
            return text
        elif fallback_filename and os.path.isfile(fallback_filename):
            text = self.load_file(fallback_filename)
            self.safe_remove(fallback_filename)
            return text

        return ''