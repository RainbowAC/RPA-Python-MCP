"""
RPA for Python - MCP Server

将 RPA for Python 的功能封装为标准 MCP (Model Context Protocol) 接口，
使 AI 助手能够通过 MCP 协议调用 RPA 自动化能力。

Usage:
    python mcp_server.py
    # 或通过 MCP 客户端配置启动
"""

import argparse
import asyncio
import concurrent.futures
import json
import sys
import os
from typing import Any, Callable, Dict

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from rpa_package import TaguiEngine

# ---------------------------------------------------------------------------
# 全局引擎实例 & 线程安全锁
# ---------------------------------------------------------------------------
_engine = TaguiEngine()
_lock = asyncio.Lock()
_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# ---------------------------------------------------------------------------
# MCP Server 初始化
# ---------------------------------------------------------------------------
server = Server("rpa-python")
_tool_registry_validated = False


# ---------------------------------------------------------------------------
# 工具定义
# ---------------------------------------------------------------------------

TOOLS = [
    # ======================== 生命周期管理 ========================
    Tool(
        name="rpa_init",
        description="初始化 RPA 引擎。必须在使用其他 RPA 工具之前调用。",
        inputSchema={
            "type": "object",
            "properties": {
                "visual_automation": {
                    "type": "boolean",
                    "description": "是否启用视觉自动化模式（基于图像识别）。默认 false。",
                    "default": False,
                },
                "chrome_browser": {
                    "type": "boolean",
                    "description": "是否使用 Chrome 浏览器。默认 true。",
                    "default": True,
                },
                "headless_mode": {
                    "type": "boolean",
                    "description": "是否使用无头模式（不显示浏览器窗口）。默认 false。",
                    "default": False,
                },
                "turbo_mode": {
                    "type": "boolean",
                    "description": "是否启用 Turbo 模式（加速执行）。默认 false。",
                    "default": False,
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_close",
        description="关闭 RPA 引擎，释放资源。自动化任务完成后应调用此方法。",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="rpa_setup",
        description="首次使用时，下载并安装 TagUI 自动化引擎到用户目录（约 200MB）。只需执行一次。",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="rpa_status",
        description="获取 RPA 引擎当前状态（是否已启动、模式等）。",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),

    # ======================== 网页导航 ========================
    Tool(
        name="rpa_url",
        description="导航到指定网页 URL，或获取当前页面 URL。需要先调用 rpa_init。",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要导航到的网页 URL（以 http:// 或 https:// 开头）。不传则返回当前 URL。",
                },
            },
            "required": [],
        },
    ),

    # ======================== 鼠标交互 ========================
    Tool(
        name="rpa_click",
        description="点击页面上的指定元素。支持 CSS 选择器、XPath、图像文件名或坐标。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "元素标识符（CSS 选择器、XPath、图像文件名如 element.png、或坐标如 (x,y)）。",
                },
            },
            "required": ["identifier"],
        },
    ),
    Tool(
        name="rpa_rclick",
        description="右键点击页面上的指定元素。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "元素标识符（CSS 选择器、XPath、图像文件名或坐标）。",
                },
            },
            "required": ["identifier"],
        },
    ),
    Tool(
        name="rpa_dclick",
        description="双击页面上的指定元素。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "元素标识符（CSS 选择器、XPath、图像文件名或坐标）。",
                },
            },
            "required": ["identifier"],
        },
    ),
    Tool(
        name="rpa_hover",
        description="鼠标悬停在指定元素上。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "元素标识符（CSS 选择器、XPath、图像文件名或坐标）。",
                },
            },
            "required": ["identifier"],
        },
    ),

    # ======================== 键盘输入 ========================
    Tool(
        name="rpa_type",
        description="在指定输入框中输入文本。支持特殊键如 [enter]、[tab]、[clear] 等。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "输入框的 CSS 选择器、XPath 或 name 属性。",
                },
                "text": {
                    "type": "string",
                    "description": "要输入的文本。可在末尾添加 [enter] 等特殊键。",
                },
            },
            "required": ["identifier", "text"],
        },
    ),
    Tool(
        name="rpa_select",
        description="在下拉选择框中选择指定选项。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "下拉选择框的 CSS 选择器或 XPath。",
                },
                "option_value": {
                    "type": "string",
                    "description": "要选择的选项值或显示文本。",
                },
            },
            "required": ["identifier", "option_value"],
        },
    ),
    Tool(
        name="rpa_keyboard",
        description="发送键盘按键组合（需要 visual_automation 模式）。如 'ctrl+c'、'enter' 等。",
        inputSchema={
            "type": "object",
            "properties": {
                "keys": {
                    "type": "string",
                    "description": "键盘按键和修饰符组合，如 '[ctrl]c'、'[enter]'。",
                },
            },
            "required": ["keys"],
        },
    ),
    Tool(
        name="rpa_mouse",
        description="发送鼠标按下/释放事件（需要 visual_automation 模式）。",
        inputSchema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "鼠标动作：'down' 或 'up'。",
                    "enum": ["down", "up"],
                },
            },
            "required": ["action"],
        },
    ),

    # ======================== 信息读取 ========================
    Tool(
        name="rpa_read",
        description="读取页面元素的内容。支持读取文本、属性值等。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "要读取的元素标识符。'page' 表示读取整个页面文本。",
                },
            },
            "required": ["identifier"],
        },
    ),
    Tool(
        name="rpa_text",
        description="获取当前页面所有可见文本内容。",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="rpa_title",
        description="获取当前页面的标题。",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="rpa_table",
        description="将页面上的表格数据保存为 CSV 文件。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "表格元素的 CSS 选择器或 XPath。",
                },
                "filename": {
                    "type": "string",
                    "description": "保存 CSV 文件的文件名。",
                },
            },
            "required": ["identifier", "filename"],
        },
    ),
    Tool(
        name="rpa_dom",
        description="在页面上执行 DOM 操作或 JavaScript 语句。",
        inputSchema={
            "type": "object",
            "properties": {
                "statement": {
                    "type": "string",
                    "description": "要执行的 DOM/JavaScript 语句。",
                },
            },
            "required": ["statement"],
        },
    ),
    Tool(
        name="rpa_timer",
        description="获取从 init() 调用以来的经过时间（秒）。",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),

    # ======================== 截图 ========================
    Tool(
        name="rpa_snap",
        description="对指定元素或页面区域截图并保存为文件。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "要截图的元素标识符。'page' 或 'page.png' 表示整个页面。",
                },
                "filename": {
                    "type": "string",
                    "description": "保存截图的目标文件名（如 screenshot.png）。",
                },
            },
            "required": ["identifier", "filename"],
        },
    ),
    Tool(
        name="rpa_snap_page",
        description="对整个页面截图并保存。",
        inputSchema={
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "保存截图的目标文件名。默认 'page.png'。",
                    "default": "page.png",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_snap_element",
        description="对指定元素截图并保存。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "要截图的元素标识符。",
                },
                "filename": {
                    "type": "string",
                    "description": "保存截图的目标文件名。默认 'element.png'。",
                    "default": "element.png",
                },
            },
            "required": ["identifier"],
        },
    ),

    # ======================== 元素检测 ========================
    Tool(
        name="rpa_exist",
        description="检查元素是否存在（会等待直到超时）。返回 true/false。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "要检查的元素标识符。",
                },
            },
            "required": ["identifier"],
        },
    ),
    Tool(
        name="rpa_present",
        description="立即检查元素是否存在（不等待）。返回 true/false。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "要检查的元素标识符。",
                },
            },
            "required": ["identifier"],
        },
    ),
    Tool(
        name="rpa_count",
        description="获取匹配指定标识符的元素数量。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "CSS 选择器或 XPath 标识符。",
                },
            },
            "required": ["identifier"],
        },
    ),

    # ======================== 文件操作 ========================
    Tool(
        name="rpa_load",
        description="从文件加载文本内容。",
        inputSchema={
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "要加载的文件路径。",
                },
            },
            "required": ["filename"],
        },
    ),
    Tool(
        name="rpa_dump",
        description="将文本内容写入文件（覆盖模式）。",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要写入的文本内容。",
                },
                "filename": {
                    "type": "string",
                    "description": "目标文件路径。",
                },
            },
            "required": ["text", "filename"],
        },
    ),
    Tool(
        name="rpa_write",
        description="将文本追加到文件末尾。",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要追加的文本内容。",
                },
                "filename": {
                    "type": "string",
                    "description": "目标文件路径。",
                },
            },
            "required": ["text", "filename"],
        },
    ),
    Tool(
        name="rpa_download",
        description="从 URL 下载文件到本地。",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "下载文件的 URL。",
                },
                "filename": {
                    "type": "string",
                    "description": "保存到本地的文件名（可选，默认从 URL 提取）。",
                },
            },
            "required": ["url"],
        },
    ),
    Tool(
        name="rpa_unzip",
        description="解压 ZIP 文件。",
        inputSchema={
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "要解压的 ZIP 文件路径。",
                },
                "location": {
                    "type": "string",
                    "description": "解压目标目录（可选，默认当前目录）。",
                },
            },
            "required": ["filepath"],
        },
    ),

    # ======================== 流程控制 ========================
    Tool(
        name="rpa_wait",
        description="等待指定的秒数。",
        inputSchema={
            "type": "object",
            "properties": {
                "seconds": {
                    "type": "number",
                    "description": "等待的秒数。默认 5 秒。",
                    "default": 5.0,
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_timeout",
        description="设置或获取元素等待超时时间（秒）。影响 exist() 等函数的等待时间。",
        inputSchema={
            "type": "object",
            "properties": {
                "seconds": {
                    "type": "number",
                    "description": "超时秒数。不传则返回当前超时设置。",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_frame",
        description="切换到指定的 iframe/frame 中进行操作。",
        inputSchema={
            "type": "object",
            "properties": {
                "main_frame": {
                    "type": "string",
                    "description": "主 frame 的 name 或 id。不传则恢复到主文档。",
                },
                "sub_frame": {
                    "type": "string",
                    "description": "嵌套子 frame 的 name 或 id（可选）。",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_popup",
        description="切换到包含指定 URL 字符串的弹出窗口/标签页。",
        inputSchema={
            "type": "object",
            "properties": {
                "url_string": {
                    "type": "string",
                    "description": "弹出窗口 URL 中包含的字符串。不传则关闭当前弹出窗口。",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_upload",
        description="上传文件到页面上的文件输入元素。",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "文件上传元素的 CSS 选择器或 XPath。",
                },
                "filepath": {
                    "type": "string",
                    "description": "要上传的本地文件路径。",
                },
            },
            "required": ["identifier", "filepath"],
        },
    ),
    Tool(
        name="rpa_download_location",
        description="设置或获取浏览器下载文件的保存目录。",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "下载保存路径。不传则返回当前路径。",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_focus",
        description="将焦点切换到指定桌面应用程序（Windows/macOS）。",
        inputSchema={
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "应用程序名称（如 'notepad'、'Safari' 等）。",
                },
            },
            "required": ["app_name"],
        },
    ),
    Tool(
        name="rpa_clipboard",
        description="读取或设置剪贴板内容（需要 visual_automation 模式）。",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要设置到剪贴板的文本。不传则返回当前剪贴板内容。",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_vision",
        description="执行视觉自动化命令（需要 visual_automation 模式）。",
        inputSchema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的视觉命令。",
                },
            },
            "required": ["command"],
        },
    ),

    # ======================== 鼠标坐标 ========================
    Tool(
        name="rpa_mouse_xy",
        description="获取当前鼠标坐标，格式为 '(x,y)'。需要 visual_automation 模式。",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="rpa_mouse_x",
        description="获取当前鼠标 X 坐标。需要 visual_automation 模式。",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="rpa_mouse_y",
        description="获取当前鼠标 Y 坐标。需要 visual_automation 模式。",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),

    # ======================== 系统命令 ========================
    Tool(
        name="rpa_run",
        description="执行系统命令并返回输出结果。",
        inputSchema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的系统命令。",
                },
            },
            "required": ["command"],
        },
    ),
    Tool(
        name="rpa_echo",
        description="输出文本到控制台（调试用）。",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要输出的文本。",
                },
            },
            "required": ["text"],
        },
    ),
    Tool(
        name="rpa_telegram",
        description="通过 Telegram 发送消息通知。",
        inputSchema={
            "type": "object",
            "properties": {
                "telegram_id": {
                    "type": "string",
                    "description": "目标 Telegram 用户 ID。",
                },
                "text": {
                    "type": "string",
                    "description": "要发送的消息文本。",
                },
            },
            "required": ["telegram_id", "text"],
        },
    ),

    # ======================== 文本处理工具 ========================
    Tool(
        name="rpa_get_text",
        description="从源文本中提取指定分隔符之间的内容。",
        inputSchema={
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "源文本。",
                },
                "left": {
                    "type": "string",
                    "description": "左侧分隔符。",
                },
                "right": {
                    "type": "string",
                    "description": "右侧分隔符。",
                },
                "count": {
                    "type": "integer",
                    "description": "第几次出现（默认 1）。",
                    "default": 1,
                },
            },
            "required": ["source", "left", "right"],
        },
    ),
    Tool(
        name="rpa_del_chars",
        description="从文本中删除指定字符。",
        inputSchema={
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "源文本。",
                },
                "characters": {
                    "type": "string",
                    "description": "要删除的字符集。",
                },
            },
            "required": ["source", "characters"],
        },
    ),
    Tool(
        name="rpa_coord",
        description="生成坐标字符串，格式为 '(x,y)'。",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {
                    "type": "integer",
                    "description": "X 坐标。默认 0。",
                    "default": 0,
                },
                "y": {
                    "type": "integer",
                    "description": "Y 坐标。默认 0。",
                    "default": 0,
                },
            },
            "required": [],
        },
    ),

    # ======================== 配置 ========================
    Tool(
        name="rpa_debug",
        description="开启或关闭调试模式。调试模式会输出更多日志信息。",
        inputSchema={
            "type": "object",
            "properties": {
                "enable": {
                    "type": "boolean",
                    "description": "是否开启调试模式。默认 true。",
                    "default": True,
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_error",
        description="开启或关闭错误模式。开启后遇到错误会抛出异常。",
        inputSchema={
            "type": "object",
            "properties": {
                "enable": {
                    "type": "boolean",
                    "description": "是否开启错误模式。默认 true。",
                    "default": True,
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_tagui_location",
        description="设置或获取 TagUI 引擎的安装路径。",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "TagUI 安装路径。不传则返回当前路径。",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="rpa_send",
        description="直接发送原始 TagUI 命令到引擎（高级用法）。",
        inputSchema={
            "type": "object",
            "properties": {
                "instruction": {
                    "type": "string",
                    "description": "要发送的原始 TagUI 指令。",
                },
            },
            "required": ["instruction"],
        },
    ),
]


# ---------------------------------------------------------------------------
# MCP 工具列表处理器
# ---------------------------------------------------------------------------

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    _validate_tool_registry()
    return TOOLS


# ---------------------------------------------------------------------------
# MCP 工具调用处理器
# ---------------------------------------------------------------------------

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    loop = asyncio.get_running_loop()
    safe_arguments = arguments or {}
    async with _lock:
        try:
            result = await loop.run_in_executor(_thread_pool, _dispatch_tool_sync, name, safe_arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]


def _dispatch_tool_sync(name: str, args: dict):
    """同步分发器，运行在线程池中避免阻塞事件循环"""
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


def _result_with_message(success: bool, success_msg: str, failed_msg: str) -> Dict[str, Any]:
    return {"success": success, "message": success_msg if success else failed_msg}


def _dispatch_rpa_init(args: Dict[str, Any]) -> Dict[str, Any]:
    success = _engine.init(
        visual_automation=args.get("visual_automation", False),
        chrome_browser=args.get("chrome_browser", True),
        headless_mode=args.get("headless_mode", False),
        turbo_mode=args.get("turbo_mode", False),
    )
    return _result_with_message(success, "RPA engine initialized", "RPA engine init failed")


def _dispatch_rpa_close(_: Dict[str, Any]) -> Dict[str, Any]:
    success = _engine.close()
    return _result_with_message(success, "RPA engine closed", "RPA engine close failed")


def _dispatch_rpa_setup(_: Dict[str, Any]) -> Dict[str, Any]:
    success = _engine.setup()
    return _result_with_message(success, "TagUI setup completed", "TagUI setup failed")


def _dispatch_rpa_status(_: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "started": _engine.started,
        "visual": _engine.visual,
        "chrome": _engine.chrome,
        "init_directory": _engine.init_directory,
        "download_directory": _engine.download_directory,
    }


def _dispatch_rpa_url(args: Dict[str, Any]) -> Dict[str, Any]:
    url = args.get("url")
    if url:
        return {"success": _engine.url(url)}
    return {"url": _engine.url()}


def _dispatch_rpa_timeout(args: Dict[str, Any]) -> Dict[str, Any]:
    if "seconds" in args:
        _engine.timeout(args["seconds"])
        return {"success": True, "timeout": _engine.config.timeout}
    return {"timeout": _engine.config.timeout}


def _dispatch_rpa_download_location(args: Dict[str, Any]) -> Dict[str, Any]:
    if "path" in args:
        return {"success": _engine.download_location(args["path"])}
    return {"path": _engine.download_location()}


def _dispatch_rpa_clipboard(args: Dict[str, Any]) -> Dict[str, Any]:
    if "text" in args:
        return {"success": _engine.clipboard(args["text"])}
    return {"content": _engine.clipboard()}


def _dispatch_rpa_tagui_location(args: Dict[str, Any]) -> Dict[str, Any]:
    if "path" in args:
        return {"location": _engine.tagui_location(args["path"])}
    return {"location": _engine.tagui_location()}


def _dispatch_rpa_debug(args: Dict[str, Any]) -> Dict[str, Any]:
    _engine.debug(args.get("enable", True))
    return {"success": True}


def _dispatch_rpa_error(args: Dict[str, Any]) -> Dict[str, Any]:
    _engine.error(args.get("enable", True))
    return {"success": True}


def _dispatch_success_with_identifier_call(args: Dict[str, Any], method_name: str) -> Dict[str, Any]:
    return {"success": getattr(_engine, method_name)(args["identifier"])}


def _dispatch_rpa_click(args: Dict[str, Any]) -> Dict[str, Any]:
    return _dispatch_success_with_identifier_call(args, "click")


def _dispatch_rpa_rclick(args: Dict[str, Any]) -> Dict[str, Any]:
    return _dispatch_success_with_identifier_call(args, "rclick")


def _dispatch_rpa_dclick(args: Dict[str, Any]) -> Dict[str, Any]:
    return _dispatch_success_with_identifier_call(args, "dclick")


def _dispatch_rpa_hover(args: Dict[str, Any]) -> Dict[str, Any]:
    return _dispatch_success_with_identifier_call(args, "hover")


def _dispatch_rpa_type(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.type(args["identifier"], args["text"])}


def _dispatch_rpa_select(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.select(args["identifier"], args["option_value"])}


def _dispatch_rpa_keyboard(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.keyboard(args["keys"])}


def _dispatch_rpa_mouse(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.mouse(args["action"])}


def _dispatch_rpa_read(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"result": _engine.read(args["identifier"])}


def _dispatch_rpa_text(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"text": _engine.text()}


def _dispatch_rpa_title(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"title": _engine.title()}


def _dispatch_rpa_table(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.table(args["identifier"], args["filename"])}


def _dispatch_rpa_dom(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"result": _engine.dom(args["statement"])}


def _dispatch_rpa_timer(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"elapsed": _engine.timer()}


def _dispatch_rpa_snap(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.snap(args["identifier"], args["filename"])}


def _dispatch_rpa_snap_page(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.snap_page(args.get("filename", "page.png"))}


def _dispatch_rpa_snap_element(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.snap_element(args["identifier"], args.get("filename", "element.png"))}


def _dispatch_rpa_exist(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"exists": _engine.exist(args["identifier"])}


def _dispatch_rpa_present(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"present": _engine.present(args["identifier"])}


def _dispatch_rpa_count(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"count": _engine.count(args["identifier"])}


def _dispatch_rpa_load(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"content": _engine.load(args["filename"])}


def _dispatch_rpa_dump(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.dump(args["text"], args["filename"])}


def _dispatch_rpa_write(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.write(args["text"], args["filename"])}


def _dispatch_rpa_download(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.download(args["url"], args.get("filename", ""))}


def _dispatch_rpa_unzip(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.unzip(args["filepath"], args.get("location"))}


def _dispatch_rpa_wait(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.wait(args.get("seconds", 5.0))}


def _dispatch_rpa_frame(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.frame(args.get("main_frame"), args.get("sub_frame"))}


def _dispatch_rpa_popup(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.popup(args.get("url_string"))}


def _dispatch_rpa_upload(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.upload(args["identifier"], args["filepath"])}


def _dispatch_rpa_focus(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.focus(args["app_name"])}


def _dispatch_rpa_vision(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.vision(args["command"])}


def _dispatch_rpa_mouse_xy(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"position": _engine.mouse_xy()}


def _dispatch_rpa_mouse_x(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"x": _engine.mouse_x()}


def _dispatch_rpa_mouse_y(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"y": _engine.mouse_y()}


def _dispatch_rpa_run(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"output": _engine.run(args["command"])}


def _dispatch_rpa_echo(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.echo(args["text"])}


def _dispatch_rpa_telegram(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.telegram(args["telegram_id"], args["text"])}


def _dispatch_rpa_get_text(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"result": _engine.get_text(args["source"], args["left"], args["right"], args.get("count", 1))}


def _dispatch_rpa_del_chars(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"result": _engine.del_chars(args["source"], args["characters"])}


def _dispatch_rpa_coord(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"coord": _engine.coord(args.get("x", 0), args.get("y", 0))}


def _dispatch_rpa_send(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": _engine.send(args["instruction"])}


_TOOL_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "rpa_init": _dispatch_rpa_init,
    "rpa_close": _dispatch_rpa_close,
    "rpa_setup": _dispatch_rpa_setup,
    "rpa_status": _dispatch_rpa_status,
    "rpa_url": _dispatch_rpa_url,
    "rpa_click": _dispatch_rpa_click,
    "rpa_rclick": _dispatch_rpa_rclick,
    "rpa_dclick": _dispatch_rpa_dclick,
    "rpa_hover": _dispatch_rpa_hover,
    "rpa_type": _dispatch_rpa_type,
    "rpa_select": _dispatch_rpa_select,
    "rpa_keyboard": _dispatch_rpa_keyboard,
    "rpa_mouse": _dispatch_rpa_mouse,
    "rpa_read": _dispatch_rpa_read,
    "rpa_text": _dispatch_rpa_text,
    "rpa_title": _dispatch_rpa_title,
    "rpa_table": _dispatch_rpa_table,
    "rpa_dom": _dispatch_rpa_dom,
    "rpa_timer": _dispatch_rpa_timer,
    "rpa_snap": _dispatch_rpa_snap,
    "rpa_snap_page": _dispatch_rpa_snap_page,
    "rpa_snap_element": _dispatch_rpa_snap_element,
    "rpa_exist": _dispatch_rpa_exist,
    "rpa_present": _dispatch_rpa_present,
    "rpa_count": _dispatch_rpa_count,
    "rpa_load": _dispatch_rpa_load,
    "rpa_dump": _dispatch_rpa_dump,
    "rpa_write": _dispatch_rpa_write,
    "rpa_download": _dispatch_rpa_download,
    "rpa_unzip": _dispatch_rpa_unzip,
    "rpa_wait": _dispatch_rpa_wait,
    "rpa_timeout": _dispatch_rpa_timeout,
    "rpa_frame": _dispatch_rpa_frame,
    "rpa_popup": _dispatch_rpa_popup,
    "rpa_upload": _dispatch_rpa_upload,
    "rpa_download_location": _dispatch_rpa_download_location,
    "rpa_focus": _dispatch_rpa_focus,
    "rpa_clipboard": _dispatch_rpa_clipboard,
    "rpa_vision": _dispatch_rpa_vision,
    "rpa_mouse_xy": _dispatch_rpa_mouse_xy,
    "rpa_mouse_x": _dispatch_rpa_mouse_x,
    "rpa_mouse_y": _dispatch_rpa_mouse_y,
    "rpa_run": _dispatch_rpa_run,
    "rpa_echo": _dispatch_rpa_echo,
    "rpa_telegram": _dispatch_rpa_telegram,
    "rpa_get_text": _dispatch_rpa_get_text,
    "rpa_del_chars": _dispatch_rpa_del_chars,
    "rpa_coord": _dispatch_rpa_coord,
    "rpa_debug": _dispatch_rpa_debug,
    "rpa_error": _dispatch_rpa_error,
    "rpa_tagui_location": _dispatch_rpa_tagui_location,
    "rpa_send": _dispatch_rpa_send,
}


def _dispatch_tool(name: str, args: dict):
    """将工具调用分发到对应的引擎方法"""
    _validate_tool_registry()
    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"Unknown tool: {name}")
    return handler(args)


# ---------------------------------------------------------------------------
# 入口点
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="RPA for Python - MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  rpa-mcp                  启动 MCP stdio 服务器（供 MCP 客户端调用）
  rpa-mcp --version        显示版本号
  rpa-mcp --list-tools     列出所有可用工具
    rpa-mcp --validate-tools 校验工具定义与分发映射是否一致
        """,
    )
    parser.add_argument(
        "--version", "-V",
        action="store_true",
        help="显示版本号",
    )
    parser.add_argument(
        "--list-tools", "-l",
        action="store_true",
        help="列出所有可用的 MCP 工具",
    )
    parser.add_argument(
        "--validate-tools",
        action="store_true",
        help="校验 MCP 工具定义与分发映射的一致性",
    )
    args = parser.parse_args()

    if args.version:
        from tagui import __version__
        print(f"rpa-mcp {__version__}")
        return

    if args.list_tools:
        print(f"共 {len(TOOLS)} 个 MCP 工具:\n")
        for tool in TOOLS:
            print(f"  {tool.name:<25s} {tool.description[:60]}")
        return

    if args.validate_tools:
        _validate_tool_registry()
        print(f"[OK] 工具注册一致性校验通过，共 {len(TOOLS)} 个 MCP 工具")
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