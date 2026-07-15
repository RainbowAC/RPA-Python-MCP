"""
Minimal desktop automation MCP server.
"""

import argparse
import asyncio
import concurrent.futures
import json
import os
import sys
from typing import Any, Callable, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from rpa_package import DesktopEngine
from rpa_package.core.config import __version__

_engine = DesktopEngine()
_lock = asyncio.Lock()
_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

server = Server("rpa-desktop")
_tool_registry_validated = False

TOOLS = [
    Tool(
        name="rpa_init",
        description="Initialize desktop automation runtime.",
        inputSchema={
            "type": "object",
            "properties": {
                "pause": {"type": "number", "default": 0.05},
                "fail_safe": {"type": "boolean", "default": True},
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_close",
        description="Close desktop automation runtime.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="rpa_status",
        description="Get runtime status.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="rpa_move_mouse",
        description="Move cursor to absolute coordinates.",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "duration": {"type": "number", "default": 0.0},
            },
            "required": ["x", "y"],
        },
    ),
    Tool(
        name="rpa_move_relative",
        description="Move cursor relative to current position.",
        inputSchema={
            "type": "object",
            "properties": {
                "dx": {"type": "integer"},
                "dy": {"type": "integer"},
                "duration": {"type": "number", "default": 0.0},
            },
            "required": ["dx", "dy"],
        },
    ),
    Tool(
        name="rpa_click",
        description="Mouse click at current cursor position.",
        inputSchema={
            "type": "object",
            "properties": {
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                "clicks": {"type": "integer", "default": 1},
                "interval": {"type": "number", "default": 0.0},
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_mouse_down",
        description="Press mouse button down.",
        inputSchema={
            "type": "object",
            "properties": {
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"}
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_mouse_up",
        description="Release mouse button.",
        inputSchema={
            "type": "object",
            "properties": {
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"}
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_drag_to",
        description="Drag cursor to absolute coordinates.",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "duration": {"type": "number", "default": 0.2},
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
            },
            "required": ["x", "y"],
        },
    ),
    Tool(
        name="rpa_drag_relative",
        description="Drag cursor by relative offset.",
        inputSchema={
            "type": "object",
            "properties": {
                "dx": {"type": "integer"},
                "dy": {"type": "integer"},
                "duration": {"type": "number", "default": 0.2},
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
            },
            "required": ["dx", "dy"],
        },
    ),
    Tool(
        name="rpa_scroll",
        description="Vertical scroll.",
        inputSchema={
            "type": "object",
            "properties": {"amount": {"type": "integer"}},
            "required": ["amount"],
        },
    ),
    Tool(
        name="rpa_hscroll",
        description="Horizontal scroll.",
        inputSchema={
            "type": "object",
            "properties": {"amount": {"type": "integer"}},
            "required": ["amount"],
        },
    ),
    Tool(
        name="rpa_type_text",
        description="Type text via keyboard.",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "interval": {"type": "number", "default": 0.0},
            },
            "required": ["text"],
        },
    ),
    Tool(
        name="rpa_press",
        description="Press one keyboard key.",
        inputSchema={
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"],
        },
    ),
    Tool(
        name="rpa_hotkey",
        description="Press combined hotkey, such as ['ctrl', 'c'].",
        inputSchema={
            "type": "object",
            "properties": {
                "keys": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["keys"],
        },
    ),
    Tool(
        name="rpa_position",
        description="Get current cursor position.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="rpa_screen_size",
        description="Get screen size.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="rpa_wait",
        description="Wait for some seconds.",
        inputSchema={
            "type": "object",
            "properties": {"seconds": {"type": "number", "default": 1.0}},
            "required": [],
        },
    ),
    Tool(
        name="rpa_debug",
        description="Enable or disable debug mode.",
        inputSchema={
            "type": "object",
            "properties": {"enable": {"type": "boolean", "default": True}},
            "required": [],
        },
    ),
    Tool(
        name="rpa_error",
        description="Enable or disable error mode.",
        inputSchema={
            "type": "object",
            "properties": {"enable": {"type": "boolean", "default": True}},
            "required": [],
        },
    ),
]


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    _validate_tool_registry()
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    loop = asyncio.get_running_loop()
    safe_arguments = arguments or {}
    async with _lock:
        try:
            result = await loop.run_in_executor(_thread_pool, _dispatch_tool_sync, name, safe_arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
        except Exception as exc:
            return [TextContent(type="text", text=json.dumps({"error": str(exc)}, ensure_ascii=False))]


def _dispatch_tool_sync(name: str, args: dict):
    return _dispatch_tool(name, args)


def _validate_tool_registry() -> None:
    global _tool_registry_validated
    if _tool_registry_validated:
        return

    tool_names = {tool.name for tool in TOOLS}
    handler_names = set(_TOOL_HANDLERS.keys())

    missing_handlers = sorted(tool_names - handler_names)
    missing_tools = sorted(handler_names - tool_names)
    if missing_handlers or missing_tools:
        errors = []
        if missing_handlers:
            errors.append(f"missing handlers for: {', '.join(missing_handlers)}")
        if missing_tools:
            errors.append(f"handlers without Tool definitions: {', '.join(missing_tools)}")
        raise RuntimeError("MCP tool registry mismatch - " + "; ".join(errors))

    _tool_registry_validated = True


def _dispatch_rpa_init(args: Dict[str, Any]) -> Dict[str, Any]:
    ok = _engine.init(pause=args.get("pause", 0.05), fail_safe=args.get("fail_safe", True))
    return {"success": ok}


def _dispatch_rpa_close(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.close()}


def _dispatch_rpa_status(_: Dict[str, Any]) -> Dict[str, Any]:
    return _engine.status()


def _dispatch_rpa_move_mouse(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.move_mouse(args["x"], args["y"], args.get("duration", 0.0))}


def _dispatch_rpa_move_relative(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.move_relative(args["dx"], args["dy"], args.get("duration", 0.0))}


def _dispatch_rpa_click(args: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "success": _engine.click(
            button=args.get("button", "left"),
            clicks=args.get("clicks", 1),
            interval=args.get("interval", 0.0),
        )
    }


def _dispatch_rpa_mouse_down(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.mouse_down(button=args.get("button", "left"))}


def _dispatch_rpa_mouse_up(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.mouse_up(button=args.get("button", "left"))}


def _dispatch_rpa_drag_to(args: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "success": _engine.drag_to(
            x=args["x"],
            y=args["y"],
            duration=args.get("duration", 0.2),
            button=args.get("button", "left"),
        )
    }


def _dispatch_rpa_drag_relative(args: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "success": _engine.drag_relative(
            dx=args["dx"],
            dy=args["dy"],
            duration=args.get("duration", 0.2),
            button=args.get("button", "left"),
        )
    }


def _dispatch_rpa_scroll(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.scroll(args["amount"])}


def _dispatch_rpa_hscroll(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.hscroll(args["amount"])}


def _dispatch_rpa_type_text(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.type_text(args["text"], args.get("interval", 0.0))}


def _dispatch_rpa_press(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.press(args["key"])}


def _dispatch_rpa_hotkey(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.hotkey(args["keys"]) }


def _dispatch_rpa_position(_: Dict[str, Any]) -> Dict[str, Any]:
    x, y = _engine.position()
    return {"x": x, "y": y}


def _dispatch_rpa_screen_size(_: Dict[str, Any]) -> Dict[str, Any]:
    width, height = _engine.screen_size()
    return {"width": width, "height": height}


def _dispatch_rpa_wait(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.wait(args.get("seconds", 1.0))}


def _dispatch_rpa_debug(args: Dict[str, Any]) -> Dict[str, Any]:
    _engine.debug(args.get("enable", True))
    return {"success": True}


def _dispatch_rpa_error(args: Dict[str, Any]) -> Dict[str, Any]:
    _engine.error(args.get("enable", True))
    return {"success": True}


_TOOL_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "rpa_init": _dispatch_rpa_init,
    "rpa_close": _dispatch_rpa_close,
    "rpa_status": _dispatch_rpa_status,
    "rpa_move_mouse": _dispatch_rpa_move_mouse,
    "rpa_move_relative": _dispatch_rpa_move_relative,
    "rpa_click": _dispatch_rpa_click,
    "rpa_mouse_down": _dispatch_rpa_mouse_down,
    "rpa_mouse_up": _dispatch_rpa_mouse_up,
    "rpa_drag_to": _dispatch_rpa_drag_to,
    "rpa_drag_relative": _dispatch_rpa_drag_relative,
    "rpa_scroll": _dispatch_rpa_scroll,
    "rpa_hscroll": _dispatch_rpa_hscroll,
    "rpa_type_text": _dispatch_rpa_type_text,
    "rpa_press": _dispatch_rpa_press,
    "rpa_hotkey": _dispatch_rpa_hotkey,
    "rpa_position": _dispatch_rpa_position,
    "rpa_screen_size": _dispatch_rpa_screen_size,
    "rpa_wait": _dispatch_rpa_wait,
    "rpa_debug": _dispatch_rpa_debug,
    "rpa_error": _dispatch_rpa_error,
}


def _dispatch_tool(name: str, args: dict):
    _validate_tool_registry()
    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"Unknown tool: {name}")
    return handler(args)


def main():
    parser = argparse.ArgumentParser(description="Desktop automation MCP server")
    parser.add_argument("--version", "-V", action="store_true", help="Show version")
    parser.add_argument("--list-tools", "-l", action="store_true", help="List MCP tools")
    parser.add_argument("--validate-tools", action="store_true", help="Validate tool registry")
    args = parser.parse_args()

    if args.version:
        print(f"rpa-mcp {__version__}")
        return

    if args.list_tools:
        print(f"Total {len(TOOLS)} tools:\n")
        for tool in TOOLS:
            print(f"  {tool.name:<24s} {tool.description}")
        return

    if args.validate_tools:
        _validate_tool_registry()
        print(f"[OK] registry is valid, tools={len(TOOLS)}")
        return

    asyncio.run(_run_server())


async def _run_server():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    main()
