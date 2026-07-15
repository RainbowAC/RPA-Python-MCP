"""
RPA for Python - Main Package Entry Point

Provides backward-compatible API: import rpa as r
"""

from .core.engine import DesktopEngine
from .core.config import __version__

_engine = DesktopEngine()

r = _engine

init = _engine.init
close = _engine.close
status = _engine.status
move_mouse = _engine.move_mouse
move_relative = _engine.move_relative
click = _engine.click
mouse_down = _engine.mouse_down
mouse_up = _engine.mouse_up
drag_to = _engine.drag_to
drag_relative = _engine.drag_relative
scroll = _engine.scroll
hscroll = _engine.hscroll
type_text = _engine.type_text
press = _engine.press
hotkey = _engine.hotkey
position = _engine.position
screen_size = _engine.screen_size
wait = _engine.wait
debug = _engine.debug
error = _engine.error

__all__ = [
    'r', 'DesktopEngine', 'init', 'close', 'status',
    'move_mouse', 'move_relative', 'click', 'mouse_down', 'mouse_up',
    'drag_to', 'drag_relative', 'scroll', 'hscroll',
    'type_text', 'press', 'hotkey', 'position', 'screen_size',
    'wait', 'debug', 'error', '__version__',
]