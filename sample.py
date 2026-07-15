"""
Minimal MCP desktop automation example.
"""

import asyncio
from mcp_server import _dispatch_tool


async def rpcall(name: str, args: dict | None = None):
    if args is None:
        args = {}
    return await asyncio.to_thread(_dispatch_tool, name, args)


async def main():
    print("Desktop automation MCP sample\n")

    r = await rpcall("rpa_init", {"pause": 0.05, "fail_safe": True})
    print(f"rpa_init         -> {r}")

    r = await rpcall("rpa_status")
    print(f"rpa_status       -> {r}")

    r = await rpcall("rpa_screen_size")
    print(f"rpa_screen_size  -> {r}")

    r = await rpcall("rpa_position")
    print(f"rpa_position     -> {r}")

    await rpcall("rpa_move_relative", {"dx": 30, "dy": 30, "duration": 0.1})
    await rpcall("rpa_click", {"button": "left", "clicks": 1})
    await rpcall("rpa_scroll", {"amount": -200})
    await rpcall("rpa_type_text", {"text": "hello from mcp", "interval": 0.02})
    await rpcall("rpa_press", {"key": "enter"})

    r = await rpcall("rpa_close")
    print(f"rpa_close        -> {r}")


if __name__ == "__main__":
    asyncio.run(main())
