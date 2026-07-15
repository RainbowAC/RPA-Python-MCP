# RPA Desktop MCP (Minimal)

一个精简版 Python 桌面自动化项目，聚焦最基础操作：

- 光标移动
- 光标点击
- 推拽
- 滚动
- 键盘输入

并保留 MCP 封装，方便 AI 助手通过标准 MCP 协议调用。

---

## 设计目标

- 去除浏览器自动化与历史下载链路
- 仅保留桌面自动化基础能力
- 减少依赖，降低维护复杂度
- 保持 MCP Server 入口与工具调用方式

---

## 项目结构

```text
RPA-Python-MCP/
├── rpa_package/
│   ├── __init__.py
│   ├── rpa.py                 # 对外 API 导出
│   └── core/
│       ├── engine.py          # 精简桌面引擎（pyautogui）
│       ├── config.py
│       ├── exceptions.py
│       └── io_helpers.py
├── mcp_server.py              # MCP 服务（桌面最小工具集）
├── mcp_config.json            # MCP 客户端配置模板
├── sample.py                  # MCP 调用示例
├── setup.py
└── README.md
```

---

## 安装

```bash
pip install -e .
```

核心依赖：

- mcp>=1.0.0
- pyautogui>=0.9.54

---

## Python API 快速开始

```python
import rpa_package.rpa as r

r.init()
r.move_mouse(500, 300, 0.2)
r.click()
r.type_text('hello')
r.press('enter')
r.close()
```

---

## MCP 服务

启动 MCP Server：

```bash
python mcp_server.py
```

或：

```bash
rpa-mcp
```

列出工具：

```bash
rpa-mcp --list-tools
```

校验工具映射：

```bash
rpa-mcp --validate-tools
```

---

## MCP 工具清单（最小集）

生命周期：

- rpa_init
- rpa_close
- rpa_status

鼠标：

- rpa_move_mouse
- rpa_move_relative
- rpa_click
- rpa_mouse_down
- rpa_mouse_up
- rpa_drag_to
- rpa_drag_relative
- rpa_scroll
- rpa_hscroll
- rpa_position
- rpa_screen_size

键盘：

- rpa_type_text
- rpa_press
- rpa_hotkey

控制与配置：

- rpa_wait
- rpa_debug
- rpa_error

---

## MCP 配置示例

参考 mcp_config.json：

```json
{
  "mcpServers": {
    "rpa-desktop": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {}
    }
  }
}
```

---

## 说明

- 本项目现在是桌面自动化最小实现，不再提供网页控制、历史 setup、文件下载/解压等原能力。
- 如需继续扩展，可在现有 MCP 映射中增量添加工具，不影响当前基础结构。
