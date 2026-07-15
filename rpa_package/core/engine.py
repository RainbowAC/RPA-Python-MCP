"""
Minimal desktop automation engine based on pyautogui.
"""

import time
from typing import Any, Optional, Sequence, Tuple

from .config import Config
from .exceptions import DesktopProcessError

class DesktopEngine:
    """Simplified desktop-only automation engine."""

    def __init__(self) -> None:
        self._config = Config()
        self._started = False
        self._last_error = ""
        self._pyautogui: Optional[Any] = None
        self._import_error: Optional[Exception] = None

    @property
    def config(self) -> Config:
        return self._config

    @property
    def started(self) -> bool:
        return self._started

    def _handle_error(self, message: str) -> bool:
        self._last_error = message
        if self._config.error_mode:
            raise DesktopProcessError(message)
        print(message)
        return False

    def _ensure_started(self) -> bool:
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before calling this method')
        return True

    def _load_pyautogui(self) -> bool:
        if self._pyautogui is not None:
            return True
        if self._import_error is not None:
            return self._handle_error(f'[RPA][ERROR] - pyautogui import failed: {self._import_error}')
        try:
            import pyautogui  # type: ignore
            self._pyautogui = pyautogui
            return True
        except Exception as exc:  # pragma: no cover - depends on runtime environment
            self._import_error = exc
            return self._handle_error(f'[RPA][ERROR] - pyautogui import failed: {exc}')

    def init(self, pause: float = 0.05, fail_safe: bool = True) -> bool:
        if not self._load_pyautogui():
            return False
        assert self._pyautogui is not None

        try:
            self._pyautogui.PAUSE = float(pause)
            self._pyautogui.FAILSAFE = bool(fail_safe)
            _ = self._pyautogui.size()
        except Exception as exc:
            return self._handle_error(f'[RPA][ERROR] - desktop automation init failed: {exc}')

        self._started = True
        return True

    def close(self) -> bool:
        self._started = False
        return True

    def status(self) -> dict:
        fail_safe = None
        pause = None
        if self._pyautogui is not None:
            fail_safe = bool(self._pyautogui.FAILSAFE)
            pause = float(self._pyautogui.PAUSE)
        return {
            'started': self._started,
            'fail_safe': fail_safe,
            'pause': pause,
            'last_error': self._last_error,
        }

    def move_mouse(self, x: int, y: int, duration: float = 0.0) -> bool:
        if not self._ensure_started():
            return False
        assert self._pyautogui is not None
        self._pyautogui.moveTo(int(x), int(y), duration=float(duration))
        return True

    def move_relative(self, dx: int, dy: int, duration: float = 0.0) -> bool:
        if not self._ensure_started():
            return False
        assert self._pyautogui is not None
        self._pyautogui.moveRel(int(dx), int(dy), duration=float(duration))
        return True

    def click(self, button: str = 'left', clicks: int = 1, interval: float = 0.0) -> bool:
        if not self._ensure_started():
            return False
        assert self._pyautogui is not None
        self._pyautogui.click(button=button, clicks=int(clicks), interval=float(interval))
        return True

    def mouse_down(self, button: str = 'left') -> bool:
        if not self._ensure_started():
            return False
        assert self._pyautogui is not None
        self._pyautogui.mouseDown(button=button)
        return True

    def mouse_up(self, button: str = 'left') -> bool:
        if not self._ensure_started():
            return False
        assert self._pyautogui is not None
        self._pyautogui.mouseUp(button=button)
        return True

    def drag_to(self, x: int, y: int, duration: float = 0.2, button: str = 'left') -> bool:
        if not self._ensure_started():
            return False
        assert self._pyautogui is not None
        self._pyautogui.dragTo(int(x), int(y), duration=float(duration), button=button)
        return True

    def drag_relative(self, dx: int, dy: int, duration: float = 0.2, button: str = 'left') -> bool:
        if not self._ensure_started():
            return False
        assert self._pyautogui is not None
        self._pyautogui.dragRel(int(dx), int(dy), duration=float(duration), button=button)
        return True

    def scroll(self, amount: int) -> bool:
        if not self._ensure_started():
            return False
        assert self._pyautogui is not None
        self._pyautogui.scroll(int(amount))
        return True

    def hscroll(self, amount: int) -> bool:
        if not self._ensure_started():
            return False
        assert self._pyautogui is not None
        self._pyautogui.hscroll(int(amount))
        return True

    def type_text(self, text: str, interval: float = 0.0) -> bool:
        if not self._ensure_started():
            return False
        assert self._pyautogui is not None
        self._pyautogui.write(str(text), interval=float(interval))
        return True

    def press(self, key: str) -> bool:
        if not self._ensure_started():
            return False
        assert self._pyautogui is not None
        self._pyautogui.press(str(key))
        return True

    def hotkey(self, keys: Sequence[str]) -> bool:
        if not self._ensure_started():
            return False
        if not keys:
            return self._handle_error('[RPA][ERROR] - keys are required for hotkey()')
        assert self._pyautogui is not None
        self._pyautogui.hotkey(*[str(k) for k in keys])
        return True

    def position(self) -> Tuple[int, int]:
        if not self._ensure_started():
            return (0, 0)
        assert self._pyautogui is not None
        pos = self._pyautogui.position()
        return (int(pos.x), int(pos.y))

    def screen_size(self) -> Tuple[int, int]:
        if not self._ensure_started():
            return (0, 0)
        assert self._pyautogui is not None
        size = self._pyautogui.size()
        return (int(size.width), int(size.height))

    @staticmethod
    def wait(seconds: float = 1.0) -> bool:
        time.sleep(float(seconds))
        return True

    def debug(self, debug_mode: bool = True) -> None:
        self._config.debug = bool(debug_mode)

    def error(self, error_mode: bool = True) -> None:
        self._config.error_mode = bool(error_mode)
