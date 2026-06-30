"""
RPA for Python - Main Package Entry Point

Provides backward-compatible API: import rpa as r
"""

from .core.engine import TaguiEngine
from .core.config import __version__

_engine = TaguiEngine()

r = _engine

init = _engine.init
close = _engine.close
send = _engine.send
url = _engine.url
click = _engine.click
rclick = _engine.rclick
dclick = _engine.dclick
hover = _engine.hover
type = _engine.type
select = _engine.select
read = _engine.read
snap = _engine.snap
snap_page = _engine.snap_page
snap_element = _engine.snap_element
table = _engine.table
upload = _engine.upload
title = _engine.title
text = _engine.text
timer = _engine.timer
frame = _engine.frame
popup = _engine.popup
dom = _engine.dom
exist = _engine.exist
present = _engine.present
count = _engine.count
keyboard = _engine.keyboard
mouse = _engine.mouse
vision = _engine.vision
mouse_xy = _engine.mouse_xy
mouse_x = _engine.mouse_x
mouse_y = _engine.mouse_y
clipboard = _engine.clipboard
focus = _engine.focus
download_location = _engine.download_location
timeout = _engine.timeout
coord = _engine.coord
wait = _engine.wait
echo = _engine.echo
check = _engine.check
ask = _engine.ask
get_text = _engine.get_text
del_chars = _engine.del_chars
load = _engine.load
dump = _engine.dump
write = _engine.write
download = _engine.download
unzip = _engine.unzip
run = _engine.run
telegram = _engine.telegram
bin = _engine.bin
pack = _engine.pack
update = _engine.update
debug = _engine.debug
error = _engine.error
tagui_location = _engine.tagui_location
setup = _engine.setup

__all__ = [
    'r', 'init', 'close', 'send', 'url', 'click', 'rclick', 'dclick', 'hover',
    'type', 'select', 'read', 'snap', 'snap_page', 'snap_element', 'table',
    'upload', 'title', 'text', 'timer', 'frame', 'popup', 'dom',
    'exist', 'present', 'count', 'keyboard', 'mouse', 'vision',
    'mouse_xy', 'mouse_x', 'mouse_y', 'clipboard', 'focus',
    'download_location', 'timeout', 'coord', 'wait', 'echo', 'check',
    'ask', 'get_text', 'del_chars', 'load', 'dump', 'write', 'download',
    'unzip', 'run', 'telegram', 'bin', 'pack', 'update', 'debug', 'error',
    'tagui_location', 'setup', '__version__',
]