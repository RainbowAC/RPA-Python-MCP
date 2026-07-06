"""
RPA for Python - MCP 工具调用示例

演示如何通过 mcp_server._dispatch_tool() 调用 MCP 工具。
"""

import asyncio
from mcp_server import _dispatch_tool


async def rpcall(name: str, args: dict = None):
    """封装 MCP 工具调用，返回结果字典"""
    if args is None:
        args = {}
    return await _dispatch_tool(name, args)


async def demo_file_text():
    """文件操作 + 文本处理（无需浏览器）"""
    print("\n--- 文件操作 + 文本处理 ---")

    r = await rpcall("rpa_dump", {
        "text": "Hello RPA\nEmail=user@example.com\nPhone=123-456-7890\n",
        "filename": "demo.txt",
    })
    print(f"rpa_dump       → {r}")

    r = await rpcall("rpa_write", {
        "text": "appended line\n",
        "filename": "demo.txt",
    })
    print(f"rpa_write      → {r}")

    r = await rpcall("rpa_load", {"filename": "demo.txt"})
    print(f"rpa_load       → {r}")

    r = await rpcall("rpa_get_text", {
        "source": "Email=user@example.com",
        "left": "Email=",
        "right": ".com",
    })
    print(f"rpa_get_text   → {r}")

    r = await rpcall("rpa_del_chars", {
        "source": "Phone: 123-456-7890",
        "characters": "-:",
    })
    print(f"rpa_del_chars  → {r}")

    r = await rpcall("rpa_coord", {"x": 100, "y": 200})
    print(f"rpa_coord      → {r}")


async def demo_system():
    """系统命令 + 配置（无需 init）"""
    print("\n--- 系统命令 + 配置 ---")

    r = await rpcall("rpa_run", {"command": "echo Hello RPA"})
    print(f"rpa_run             → {r}")

    r = await rpcall("rpa_echo", {"text": "控制台输出测试"})
    print(f"rpa_echo            → {r}")

    r = await rpcall("rpa_tagui_location")
    print(f"rpa_tagui_location  → {r}")

    r = await rpcall("rpa_debug", {"enable": False})
    print(f"rpa_debug           → {r}")

    r = await rpcall("rpa_error", {"enable": True})
    print(f"rpa_error           → {r}")


async def demo_browser_basic():
    """浏览器基础操作：init → url → 检测 → 输入 → 读取 → close"""
    print("\n--- 浏览器基础操作 ---")

    r = await rpcall("rpa_init", {
        "visual_automation": False,
        "chrome_browser": True,
        "turbo_mode": True,
    })
    if not r.get("success"):
        print("rpa_init 失败，跳过浏览器场景")
        return
    print(f"rpa_init        → {r}")

    r = await rpcall("rpa_status")
    print(f"rpa_status      → {r}")

    r = await rpcall("rpa_timeout", {"seconds": 30})
    print(f"rpa_timeout     → {r}")

    r = await rpcall("rpa_send", {"instruction": "echo raw command"})
    print(f"rpa_send        → {r}")

    await rpcall("rpa_url", {"url": "https://www.bing.com"})
    print("rpa_url         → done")

    await rpcall("rpa_wait", {"seconds": 2})

    r = await rpcall("rpa_title")
    print(f"rpa_title       → {r}")

    r = await rpcall("rpa_timer")
    print(f"rpa_timer       → {r}")

    r = await rpcall("rpa_present", {"identifier": "#sb_form_q"})
    print(f"rpa_present     → {r}")

    r = await rpcall("rpa_count", {"identifier": "input"})
    print(f"rpa_count       → {r}")

    r = await rpcall("rpa_exist", {"identifier": "#sb_form_q"})
    print(f"rpa_exist       → {r}")

    r = await rpcall("rpa_type", {
        "identifier": "#sb_form_q",
        "text": "RPA automation[enter]",
    })
    print(f"rpa_type        → {r}")

    await rpcall("rpa_wait", {"seconds": 2})

    r = await rpcall("rpa_read", {"identifier": "page"})
    preview = (r.get("result", "") or "")[:80]
    print(f"rpa_read(page)  → {preview}...")

    r = await rpcall("rpa_text")
    preview = (r.get("text", "") or "")[:80]
    print(f"rpa_text        → {preview}...")

    r = await rpcall("rpa_dom", {"statement": "document.title"})
    print(f"rpa_dom         → {r}")

    r = await rpcall("rpa_close")
    print(f"rpa_close       → {r}")


async def demo_browser_interact():
    """浏览器交互：点击、悬停、选择、截图"""
    print("\n--- 浏览器交互 ---")

    r = await rpcall("rpa_init", {
        "visual_automation": False,
        "chrome_browser": True,
    })
    if not r.get("success"):
        print("rpa_init 失败，跳过")
        return

    await rpcall("rpa_url", {"url": "https://www.bing.com"})
    await rpcall("rpa_wait", {"seconds": 2})

    sel = "#sb_form_q"

    r = await rpcall("rpa_click", {"identifier": sel})
    print(f"rpa_click       → {r}")

    r = await rpcall("rpa_hover", {"identifier": sel})
    print(f"rpa_hover       → {r}")

    r = await rpcall("rpa_dclick", {"identifier": sel})
    print(f"rpa_dclick      → {r}")

    r = await rpcall("rpa_rclick", {"identifier": sel})
    print(f"rpa_rclick      → {r}")

    r = await rpcall("rpa_select", {
        "identifier": sel,
        "option_value": "search",
    })
    print(f"rpa_select      → {r}")

    r = await rpcall("rpa_snap", {
        "identifier": sel,
        "filename": "element.png",
    })
    print(f"rpa_snap        → {r}")

    r = await rpcall("rpa_snap_element", {
        "identifier": sel,
        "filename": "snap_element.png",
    })
    print(f"rpa_snap_element → {r}")

    await rpcall("rpa_close")


async def main():
    print("RPA for Python — MCP 工具调用示例\n")

    await demo_file_text()
    await demo_system()
    await demo_browser_basic()
    await demo_browser_interact()

    print("\n全部示例完成")


if __name__ == "__main__":
    asyncio.run(main())