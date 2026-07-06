# RPA for Python

简单而强大的 Python 机器人流程自动化（RPA）库，支持浏览器自动化、桌面应用自动化和命令行操作。内置 MCP（Model Context Protocol）集成，AI 助手可直接调用 RPA 能力。

[![Python](https://img.shields.io/badge/Python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()

---

## 项目结构

```
RPA-Python-master/
├── rpa_package/              # 核心 RPA 引擎包
│   ├── __init__.py
│   ├── rpa.py                # 面向用户的 API（import rpa as r）
│   ├── setup.py              # 包内 TagUI 部署逻辑
│   └── core/
│       ├── engine.py         # 引擎核心，方法分发
│       ├── config.py         # 配置管理
│       ├── exceptions.py     # 自定义异常
│       └── io_helpers.py     # 文件/IO 辅助
├── mcp_server.py             # MCP 服务器，暴露 40+ 个 MCP 工具
├── mcp_config.json           # MCP 客户端配置模板
├── sample.py                 # MCP 工具调用完整示例
├── tagui.py                  # 顶层 TagUI 兼容模块
├── setup.py                  # 项目安装配置
└── README.md
```

---

## 特性

- **简单 API**：`import rpa as r` 即可开始，一行代码完成浏览器导航、点击、输入等操作
- **浏览器自动化**：基于 Chrome DevTools Protocol，支持 Chrome 和 Headless 无头模式
- **视觉自动化**：基于 SikuliX 图像识别，支持桌面应用的 GUI 自动化
- **MCP 集成**：内置 MCP 服务器，AI 助手（如 Claude、Cursor）可通过标准协议操控浏览器和桌面
- **跨平台**：支持 Windows、macOS、Linux
- **自动部署**：首次使用时自动下载安装 TagUI 引擎（~200MB），无需手动配置

---

## 安装

```bash
pip install rpa
```

MCP 集成支持：

```bash
pip install rpa[mcp]
```

---

## 快速开始

```python
import rpa as r

r.init()
r.url('https://www.google.com')
r.type('q', 'decentralization[enter]')
print(r.title())
r.snap('page', 'results.png')
r.close()
```

### 更多模式

```python
r.init(visual_automation=True)   # 视觉自动化（桌面应用）
r.init(headless_mode=True)       # 无头模式
r.init(turbo_mode=True)          # Turbo 加速
```

---

## API 参考

### 生命周期管理

| 方法 | 说明 |
|------|------|
| `init(visual_automation=False, chrome_browser=True, headless_mode=False, turbo_mode=False)` | 初始化 RPA 引擎 |
| `close()` | 关闭引擎，释放资源 |
| `setup()` | 首次使用时下载安装 TagUI 引擎 |
| `send(instruction)` | 发送原始 TagUI 指令 |

### 网页导航

| 方法 | 说明 |
|------|------|
| `url(url)` | 导航到指定 URL，不传参数则返回当前 URL |

### 鼠标交互

| 方法 | 说明 |
|------|------|
| `click(identifier)` | 点击元素 |
| `rclick(identifier)` | 右键点击 |
| `dclick(identifier)` | 双击 |
| `hover(identifier)` | 鼠标悬停 |

> `identifier` 支持 CSS 选择器、XPath、图像文件名（如 `button.png`）或坐标（如 `(100,200)`）

### 键盘输入

| 方法 | 说明 |
|------|------|
| `type(identifier, text)` | 在输入框中输入文本，支持特殊键如 `[enter]`、`[tab]`、`[clear]` |
| `select(identifier, option)` | 在下拉选择框中选择选项 |
| `keyboard(keys)` | 发送键盘组合键（需 visual_automation），如 `[ctrl]c` |
| `mouse(action)` | 发送鼠标按下/释放事件（需 visual_automation） |

### 信息读取

| 方法 | 说明 |
|------|------|
| `read(identifier)` | 读取元素内容，`'page'` 读取整个页面文本 |
| `text()` | 获取页面所有可见文本 |
| `title()` | 获取页面标题 |
| `table(identifier, filename)` | 将表格数据保存为 CSV 文件 |
| `dom(statement)` | 在页面上执行 DOM/JavaScript 语句 |
| `timer()` | 获取从 init() 以来的经过时间（秒） |

### 元素检测

| 方法 | 说明 |
|------|------|
| `exist(identifier)` | 等待元素出现（直到超时），返回 bool |
| `present(identifier)` | 立即检查元素是否存在，返回 bool |
| `count(identifier)` | 获取匹配元素的数量 |

### 截图

| 方法 | 说明 |
|------|------|
| `snap(identifier, filename)` | 对指定元素截图保存 |
| `snap_page(filename)` | 对整个页面截图保存 |
| `snap_element(identifier, filename)` | 对指定元素截图保存 |

### 流程控制

| 方法 | 说明 |
|------|------|
| `wait(seconds)` | 等待指定秒数 |
| `timeout(seconds)` | 设置/获取元素等待超时时间 |
| `frame(main_frame, sub_frame)` | 切换到指定 iframe/frame |
| `popup(url_string)` | 切换到包含指定 URL 的弹出窗口 |
| `upload(identifier, filepath)` | 上传文件 |
| `download_location(path)` | 设置/获取下载文件保存目录 |
| `focus(app_name)` | 切换焦点到指定桌面应用程序 |
| `clipboard(text)` | 读取/设置剪贴板内容（需 visual_automation） |
| `vision(command)` | 执行视觉自动化命令（需 visual_automation） |

### 鼠标坐标（需 visual_automation）

| 方法 | 说明 |
|------|------|
| `mouse_xy()` | 获取当前鼠标坐标 `(x,y)` |
| `mouse_x()` | 获取当前鼠标 X 坐标 |
| `mouse_y()` | 获取当前鼠标 Y 坐标 |

### 文件操作

| 方法 | 说明 |
|------|------|
| `load(filename)` | 从文件加载文本内容 |
| `dump(text, filename)` | 将文本写入文件（覆盖） |
| `write(text, filename)` | 将文本追加到文件末尾 |
| `download(url, filename)` | 从 URL 下载文件 |
| `unzip(filepath, location)` | 解压 ZIP 文件 |

### 工具函数

| 方法 | 说明 |
|------|------|
| `coord(x, y)` | 生成坐标字符串 `(x,y)` |
| `echo(text)` | 输出文本到控制台 |
| `check(condition, true_text, false_text)` | 条件判断并输出对应文本 |
| `ask(prompt)` | 提示用户输入 |
| `get_text(source, left, right, count)` | 从文本中提取分隔符之间的内容 |
| `del_chars(source, characters)` | 从文本中删除指定字符 |
| `run(command)` | 执行系统命令并返回输出 |
| `telegram(telegram_id, text)` | 通过 Telegram 发送消息 |

### 配置

| 方法 | 说明 |
|------|------|
| `debug(enable)` | 开启/关闭调试模式 |
| `error(enable)` | 开启/关闭错误模式（抛出异常 vs 打印错误） |
| `tagui_location(path)` | 设置/获取 TagUI 安装路径 |

---

## MCP 集成

RPA for Python 内置 MCP 服务器，让 AI 助手能够直接调用 RPA 自动化能力。

### 启动 MCP 服务器

```bash
python mcp_server.py

# 或通过控制台入口
rpa-mcp
```

### 在 AI 客户端中配置

参考 [mcp_config.json](mcp_config.json)，在 Claude Desktop 或其他 MCP 客户端中添加：

```json
{
  "mcpServers": {
    "rpa-python": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {}
    }
  }
}
```

### MCP 工具调用示例

参见 [sample.py](sample.py) — 完整演示了全部 40+ 个 MCP 工具的调用方式：

```bash
python sample.py
```

示例涵盖：

| 场景 | 涉及工具 |
|------|----------|
| 文件操作 + 文本处理 | `dump / write / load / get_text / del_chars / coord` |
| 系统命令 + 配置 | `run / echo / tagui_location / debug / error` |
| 浏览器基础操作 | `init → status → timeout → send → url → title → timer → present → count → exist → type → read → text → dom → close` |
| 浏览器交互 | `click / hover / dclick / rclick / select / snap / snap_element` |

### 可用 MCP 工具（40+）

所有 API 方法均通过 MCP 工具暴露，命名规则为 `rpa_` 前缀，参数与 API 方法一一对应。

---

## 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `timeout` | `10.0` 秒 | 元素等待超时时间 |
| `delay` | `0.1` 秒 | 轮询间隔 |
| `debug` | `False` | 调试模式，输出更多日志 |
| `error_mode` | `False` | 错误时抛出异常而非打印 |
| `tagui_location` | Windows: `%APPDATA%`，其他: `~` | TagUI 安装路径 |

```python
import rpa as r

r.init()
r.timeout(30)      # 设置超时为 30 秒
r.debug(True)       # 开启调试模式
r.error(True)       # 开启错误模式
```

---

## 平台支持

| 操作系统 | 浏览器自动化 | 视觉自动化 | 说明 |
|----------|:----------:|:--------:|------|
| Windows  | ✅ | ✅ | 需要 Visual C++ Redistributable |
| macOS    | ✅ | ✅ | 需要 OpenJDK v8+ (64-bit) |
| Linux    | ✅ | ⚠️ | 视觉自动化需安装 OpenCV 和 Tesseract |

---

## 依赖

- **Python** 3.6+
- **TagUI** 自动化引擎（首次运行时自动下载安装，~200MB）
- **MCP**（可选）：`mcp>=1.0.0`，用于 AI 助手集成

---

## 示例

### 网页表单自动填写

```python
import rpa as r

r.init()
r.url('https://httpbin.org/forms/post')
r.type('input[name="custname"]', '张三')
r.type('input[name="custtel"]', '13800138000')
r.type('input[name="custemail"]', 'zhangsan@example.com')
r.select('select[name="size"]', 'medium')
r.type('input[name="delivery"]', '2025-01-15')
r.click('button[type="submit"]')
print(r.read('body'))
r.close()
```

### 数据采集

```python
import rpa as r

r.init()
r.url('https://www.example.com/data')

if r.exist('table.data-table'):
    r.table('table.data-table', 'data.csv')
    print('数据已保存到 data.csv')

content = r.read('page')
print(content)
r.close()
```

### 桌面应用自动化（视觉模式）

```python
import rpa as r

r.init(visual_automation=True)
r.focus('Calculator')
r.click('button_7.png')
text = r.clipboard()
print(text)
r.close()
```

---

## 许可证

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)