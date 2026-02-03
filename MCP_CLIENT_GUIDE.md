# MCP 服务连接和使用指南

## 📋 目录

1. [MCP 服务简介](#mcp-服务简介)
2. [连接方式概览](#连接方式概览)
3. [方式一：Claude Desktop 集成](#方式一claude-desktop-集成)
4. [方式二：Python 客户端](#方式二python-客户端)
5. [方式三：其他 MCP 客户端](#方式三其他-mcp-客户端)
6. [可用工具列表](#可用工具列表)
7. [实际使用示例](#实际使用示例)
8. [故障排除](#故障排除)

---

## MCP 服务简介

### 什么是 MCP？

**MCP (Model Context Protocol)** 是 Anthropic 开发的一个开放协议，用于连接 AI 模型和外部工具/数据源。

### 本 MCP 服务功能

这个 `kali-driver-mcp` 服务提供了 **9 个工具**，用于远程管理 Kali Linux 虚拟机中的网卡驱动开发和调试：

- 内核信息查询
- 文件操作（列表、读取、搜索）
- 共享文件夹验证
- 驱动编译
- 驱动加载/卸载
- 日志查看
- 网络接口信息
- 监控模式管理
- 数据包捕获

### 架构图

```
┌─────────────────────────────────┐
│   MCP 客户端                     │
│   (Claude Desktop, Python, etc) │
│            ↕ stdio               │
│   kali-driver-mcp 服务器         │
│            ↕ SSH                 │
│   Kali Linux VM                  │
└─────────────────────────────────┘
```

---

## 连接方式概览

| 连接方式 | 适用场景 | 难度 | 交互方式 |
|---------|---------|------|---------|
| **Claude Desktop** | 日常使用，自然语言交互 | ⭐ 简单 | 对话式 |
| **Python 客户端** | 自动化脚本，批量操作 | ⭐⭐ 中等 | 编程式 |
| **其他工具** | 集成到现有工作流 | ⭐⭐⭐ 复杂 | 取决于工具 |

---

## 方式一：Claude Desktop 集成

### 适用场景

- ✅ 希望通过自然语言与 Kali VM 交互
- ✅ 快速调试驱动问题
- ✅ 不需要编写代码

### 步骤 1: 确保 MCP 服务已安装

```bash
# 进入项目目录
cd /path/to/kali-driver-mcp

# 确认依赖已安装
uv sync

# 验证服务可以运行
uv run python -m kali_driver_mcp.server --help
```

### 步骤 2: 配置 config.yaml

```bash
# 如果还没有配置文件，复制示例
cp config.yaml.example config.yaml

# 编辑配置文件
nano config.yaml
```

**关键配置项**：

```yaml
vm:
  host: "192.168.2.104"        # 你的 Kali VM IP
  port: 22
  username: "kali"
  auth_method: "password"      # 或 "key"
  password: "kali"             # 或留空使用 key_file
  key_file: ""                 # SSH 密钥路径（如果使用密钥认证）
  use_sudo: true               # 是否需要 sudo
  sudo_method: "su"            # sudo 方式

shared_folder:
  host_path: "/Users/你的用户名/driver-code"
  vm_path: "/home/kali/Desktop/share/driver-code"
  verify_mount: true

logging:
  level: "INFO"                # 生产环境建议用 INFO
  file: "logs/kali-driver-mcp.log"
  enable_console: false        # Claude Desktop 不需要控制台日志
```

### 步骤 3: 配置 Claude Desktop

**macOS 配置文件位置**：
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux 配置文件位置**：
```
~/.config/Claude/claude_desktop_config.json
```

**Windows 配置文件位置**：
```
%APPDATA%\Claude\claude_desktop_config.json
```

**配置内容**：

```json
{
  "mcpServers": {
    "kali-driver": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "kali_driver_mcp.server",
        "--config",
        "/完整路径/kali-driver-mcp/config.yaml"
      ],
      "cwd": "/完整路径/kali-driver-mcp"
    }
  }
}
```

**重要提示**：
- ✅ 使用**完整路径**，不要使用 `~` 或相对路径
- ✅ 路径中不能有空格（或使用引号包围）
- ✅ macOS/Linux 使用 `/`，Windows 使用 `\\`

**配置示例（macOS）**：

```json
{
  "mcpServers": {
    "kali-driver": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "kali_driver_mcp.server",
        "--config",
        "/Users/haoyang/src/python/kali-driver-mcp/config.yaml"
      ],
      "cwd": "/Users/haoyang/src/python/kali-driver-mcp"
    }
  }
}
```

### 步骤 4: 重启 Claude Desktop

1. 完全退出 Claude Desktop（macOS: Cmd+Q）
2. 重新启动 Claude Desktop
3. 在新对话中应该能看到 MCP 工具图标（🔨 或类似）

### 步骤 5: 验证连接

在 Claude Desktop 中输入：

```
请列出 Kali VM 中的可用网络接口
```

或者：

```
使用 kernel_info 工具查看内核版本
```

如果成功，Claude 会调用 MCP 工具并返回结果。

---

## 方式二：Python 客户端

### 适用场景

- ✅ 需要自动化脚本
- ✅ 批量操作
- ✅ 集成到现有 Python 项目
- ✅ 不依赖 Claude Desktop

### 步骤 1: 安装依赖

```bash
# 创建新的 Python 项目
mkdir my-kali-automation
cd my-kali-automation

# 初始化 UV 项目
uv init

# 安装 MCP 客户端库
uv add mcp
```

### 步骤 2: 创建客户端脚本

创建 `client.py`：

```python
"""自定义 MCP 客户端 - 连接到 kali-driver-mcp 服务."""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """主函数."""

    # 配置 MCP 服务器参数
    server_params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "python",
            "-m",
            "kali_driver_mcp.server",
            "--config",
            "/完整路径/kali-driver-mcp/config.yaml"
        ],
        # 工作目录
        cwd="/完整路径/kali-driver-mcp"
    )

    # 连接到 MCP 服务器
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            print("✅ 已连接到 MCP 服务器\n")

            # 列出可用工具
            tools = await session.list_tools()
            print("📋 可用工具:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            print("\n" + "="*60 + "\n")

            # 示例 1: 获取内核信息
            print("🔍 示例 1: 获取内核信息")
            result = await session.call_tool(
                "kernel_info",
                {"detail_level": "basic"}
            )
            data = json.loads(result.content[0].text)
            print(f"  版本: {data.get('version', 'N/A')}")
            print(f"  架构: {data.get('architecture', 'N/A')}\n")

            # 示例 2: 验证共享文件夹
            print("🔍 示例 2: 验证共享文件夹")
            result = await session.call_tool("code_sync", {})
            data = json.loads(result.content[0].text)
            print(f"  状态: {'✅ 就绪' if data.get('ready') else '❌ 未就绪'}")
            print(f"  VM 路径: {data.get('vm_path', 'N/A')}\n")

            # 示例 3: 列出共享文件夹中的文件
            print("🔍 示例 3: 列出共享文件夹文件")
            result = await session.call_tool(
                "file_ops",
                {
                    "operation": "list",
                    "recursive": False
                }
            )
            data = json.loads(result.content[0].text)
            files = data.get('files', [])
            print(f"  文件数量: {len(files)}")
            for f in files[:5]:  # 只显示前5个
                print(f"    - {f['name']} ({f['type']})")

            print("\n✅ 所有示例执行完成!")


if __name__ == "__main__":
    asyncio.run(main())
```

### 步骤 3: 运行客户端

```bash
# 确保 kali-driver-mcp 服务配置正确
cd /path/to/kali-driver-mcp
cat config.yaml  # 检查配置

# 运行客户端
cd /path/to/my-kali-automation
uv run python client.py
```

### 高级示例：编译和加载驱动

```python
async def compile_and_load_driver(session: ClientSession):
    """编译并加载驱动的完整流程."""

    try:
        # 1. 验证共享文件夹
        print("📁 验证共享文件夹...")
        result = await session.call_tool("code_sync", {})
        data = json.loads(result.content[0].text)
        if not data.get('ready'):
            print("❌ 共享文件夹未就绪")
            return

        # 2. 编译驱动
        print("🔨 编译驱动...")
        result = await session.call_tool(
            "driver_compile",
            {
                "clean": True,
                "verbose": True
            }
        )
        data = json.loads(result.content[0].text)
        if not data.get('success'):
            print(f"❌ 编译失败: {data.get('error')}")
            return
        print(f"✅ 编译成功")

        # 3. 加载驱动
        print("📦 加载驱动...")
        result = await session.call_tool(
            "driver_load",
            {
                "operation": "load",
                "module_name": "mydriver",
                "parameters": {
                    "debug": "1"
                }
            }
        )
        data = json.loads(result.content[0].text)
        if data.get('success'):
            print(f"✅ 驱动加载成功")
        else:
            print(f"❌ 驱动加载失败: {data.get('error')}")

        # 4. 查看内核日志
        print("📋 查看内核日志...")
        result = await session.call_tool(
            "log_viewer",
            {
                "source": "dmesg",
                "lines": 20,
                "filter_pattern": "mydriver"
            }
        )
        data = json.loads(result.content[0].text)
        print("日志内容:")
        for line in data.get('logs', [])[:10]:
            print(f"  {line}")

        print("\n✅ 完整流程执行成功!")

    except Exception as e:
        print(f"❌ 错误: {e}")
```

---

## 方式三：其他 MCP 客户端

### 支持 MCP 协议的工具

1. **Claude Desktop** （官方）
2. **Continue.dev** （VS Code / JetBrains 插件）
3. **Zed Editor** （内置 MCP 支持）
4. **自定义客户端** （任何支持 stdio 的程序）

### Continue.dev 配置示例

**配置文件位置**：`~/.continue/config.json`

```json
{
  "mcpServers": [
    {
      "name": "kali-driver",
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "kali_driver_mcp.server",
        "--config",
        "/完整路径/kali-driver-mcp/config.yaml"
      ],
      "cwd": "/完整路径/kali-driver-mcp"
    }
  ]
}
```

### Zed Editor 配置示例

**配置文件**：Zed Settings → Extensions → MCP

```json
{
  "mcp_servers": {
    "kali-driver": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "kali_driver_mcp.server",
        "--config",
        "/完整路径/kali-driver-mcp/config.yaml"
      ],
      "cwd": "/完整路径/kali-driver-mcp"
    }
  }
}
```

---

## 可用工具列表

### 1. kernel_info

**功能**：获取 Kali VM 的内核版本和配置信息

**参数**：
```json
{
  "detail_level": "basic"  // "basic" 或 "full"
}
```

**示例（Claude Desktop）**：
```
使用 kernel_info 工具查看内核版本
```

**示例（Python）**：
```python
result = await session.call_tool("kernel_info", {"detail_level": "full"})
```

---

### 2. file_ops

**功能**：列出、读取、搜索共享文件夹中的文件

**参数**：
```json
{
  "operation": "list",        // "list", "read", "stat", "search"
  "path": "/path/to/file",    // 可选，默认为共享文件夹
  "recursive": false,         // 是否递归
  "filter_pattern": "*.c",    // 文件过滤模式
  "search_pattern": "regex"   // 搜索内容（用于 search 操作）
}
```

**示例**：
```
列出共享文件夹中所有 .c 文件
```

---

### 3. code_sync

**功能**：验证共享文件夹是否正确挂载

**参数**：无

**示例**：
```
验证共享文件夹是否可访问
```

---

### 4. driver_compile

**功能**：编译驱动模块

**参数**：
```json
{
  "target": "all",     // make 目标，可选
  "clean": false,      // 是否先清理
  "verbose": false     // 是否详细输出
}
```

**示例**：
```
清理并编译驱动，显示详细输出
```

---

### 5. driver_load

**功能**：加载、卸载、重载内核模块

**参数**：
```json
{
  "operation": "load",      // "load", "unload", "reload", "info", "list"
  "module_name": "mydriver", // 模块名（不含 .ko）
  "parameters": {           // 模块参数（可选）
    "debug": "1",
    "mode": "test"
  },
  "force": false            // 强制卸载
}
```

**示例**：
```
加载驱动 mydriver，设置 debug=1
```

---

### 6. log_viewer

**功能**：查看内核和系统日志

**参数**：
```json
{
  "source": "dmesg",           // "dmesg", "syslog", "kern", "journal"
  "lines": 50,                 // 行数
  "filter_pattern": "mydriver", // 过滤模式
  "level": "error",            // 日志级别
  "since": "5 min ago"         // 时间过滤
}
```

**示例**：
```
查看最近 50 行 dmesg 日志，过滤包含 mydriver 的内容
```

---

### 7. network_info

**功能**：获取网络接口信息

**参数**：
```json
{
  "interface": "all",        // 接口名或 "all"
  "detail_level": "basic",   // "basic", "detailed", "statistics"
  "info_type": "status"      // "status", "driver", "settings", "stats"
}
```

**示例**：
```
显示所有网络接口的详细信息
```

---

### 8. network_monitor

**功能**：启动/停止无线监控模式

**参数**：
```json
{
  "operation": "start",  // "start", "stop", "status"
  "channel": 6           // 频道号（仅 start 需要）
}
```

**示例**：
```
在频道 6 启动监控模式
```

---

### 9. packet_capture

**功能**：捕获无线数据包

**参数**：
```json
{
  "channel": 6,                  // 频道号（可选）
  "bssid": "AA:BB:CC:DD:EE:FF",  // 目标 AP（可选）
  "duration": 60,                // 持续时间（秒）
  "output_prefix": "capture"     // 输出文件前缀
}
```

**示例**：
```
在频道 6 捕获数据包 60 秒
```

---

## 实际使用示例

### 场景 1: 开发调试驱动（Claude Desktop）

**与 Claude 的对话**：

```
你: 我正在开发一个网卡驱动，需要编译和测试。

Claude: 好的，让我帮你完成这个流程。首先验证共享文件夹...
[Claude 调用 code_sync 工具]

Claude: 共享文件夹已就绪。现在编译驱动...
[Claude 调用 driver_compile 工具]

Claude: 编译成功！现在加载驱动...
[Claude 调用 driver_load 工具]

Claude: 驱动已加载。让我查看内核日志看是否有问题...
[Claude 调用 log_viewer 工具]

Claude: 驱动加载成功，日志显示没有错误。
```

---

### 场景 2: 批量测试驱动（Python 脚本）

```python
"""批量测试驱动脚本."""

import asyncio
import json
from datetime import datetime
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_driver_cycle(session: ClientSession, module_name: str, test_params: dict):
    """测试单次驱动加载-测试-卸载循环."""

    print(f"\n{'='*60}")
    print(f"测试: {module_name} | 参数: {test_params}")
    print(f"{'='*60}\n")

    try:
        # 1. 卸载已有模块
        print("🗑️  卸载旧模块...")
        await session.call_tool(
            "driver_load",
            {"operation": "unload", "module_name": module_name, "force": True}
        )

        # 2. 编译驱动
        print("🔨 编译驱动...")
        result = await session.call_tool(
            "driver_compile",
            {"clean": True, "verbose": False}
        )
        data = json.loads(result.content[0].text)
        if not data.get('success'):
            print(f"❌ 编译失败")
            return {"success": False, "stage": "compile"}

        # 3. 加载驱动（带参数）
        print("📦 加载驱动...")
        result = await session.call_tool(
            "driver_load",
            {
                "operation": "load",
                "module_name": module_name,
                "parameters": test_params
            }
        )
        data = json.loads(result.content[0].text)
        if not data.get('success'):
            print(f"❌ 加载失败")
            return {"success": False, "stage": "load"}

        # 4. 等待几秒让驱动初始化
        await asyncio.sleep(3)

        # 5. 检查网络接口
        print("🌐 检查网络接口...")
        result = await session.call_tool(
            "network_info",
            {"interface": "wlan0", "detail_level": "detailed"}
        )

        # 6. 查看内核日志
        print("📋 检查内核日志...")
        result = await session.call_tool(
            "log_viewer",
            {
                "source": "dmesg",
                "lines": 30,
                "filter_pattern": module_name
            }
        )
        data = json.loads(result.content[0].text)
        logs = data.get('logs', [])

        # 检查是否有错误
        errors = [log for log in logs if 'error' in log.lower() or 'fail' in log.lower()]

        if errors:
            print(f"⚠️  发现 {len(errors)} 个错误:")
            for err in errors[:5]:
                print(f"  {err}")
            return {"success": False, "stage": "runtime", "errors": errors}

        print("✅ 测试通过!")
        return {"success": True, "logs": logs}

    except Exception as e:
        print(f"❌ 异常: {e}")
        return {"success": False, "stage": "exception", "error": str(e)}


async def main():
    """主测试流程."""

    # 测试配置
    test_cases = [
        {"debug": "0", "mode": "normal"},
        {"debug": "1", "mode": "normal"},
        {"debug": "1", "mode": "test"},
    ]

    module_name = "mydriver"
    results = []

    server_params = StdioServerParameters(
        command="uv",
        args=[
            "run", "python", "-m", "kali_driver_mcp.server",
            "--config", "/path/to/config.yaml"
        ],
        cwd="/path/to/kali-driver-mcp"
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print(f"🚀 开始批量测试: {len(test_cases)} 个测试用例")
            print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            for i, params in enumerate(test_cases, 1):
                print(f"\n{'='*60}")
                print(f"测试用例 {i}/{len(test_cases)}")
                print(f"{'='*60}")

                result = await test_driver_cycle(session, module_name, params)
                results.append({
                    "case": i,
                    "params": params,
                    "result": result
                })

                # 测试间隔
                if i < len(test_cases):
                    print("\n⏸️  等待 5 秒...")
                    await asyncio.sleep(5)

            # 输出汇总
            print(f"\n{'='*60}")
            print("📊 测试汇总")
            print(f"{'='*60}\n")

            passed = sum(1 for r in results if r['result'].get('success'))
            failed = len(results) - passed

            print(f"总测试数: {len(results)}")
            print(f"✅ 通过: {passed}")
            print(f"❌ 失败: {failed}")
            print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            if failed > 0:
                print("失败的测试:")
                for r in results:
                    if not r['result'].get('success'):
                        print(f"  - 用例 {r['case']}: {r['params']} -> {r['result'].get('stage')}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### 场景 3: 自动化数据包捕获（Python）

```python
"""自动化抓包脚本."""

import asyncio
import json
from datetime import datetime


async def capture_workflow(session, channels: list[int], duration: int):
    """在多个频道上自动抓包."""

    print("🚀 开始自动抓包流程\n")

    # 1. 启动监控模式
    print("📡 启动监控模式...")
    result = await session.call_tool(
        "network_monitor",
        {"operation": "start"}
    )
    await asyncio.sleep(2)

    # 2. 在每个频道上抓包
    for channel in channels:
        print(f"\n📻 频道 {channel} 抓包 ({duration}秒)...")

        # 设置频道并抓包
        await session.call_tool(
            "network_monitor",
            {"operation": "start", "channel": channel}
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_prefix = f"ch{channel}_{timestamp}"

        result = await session.call_tool(
            "packet_capture",
            {
                "channel": channel,
                "duration": duration,
                "output_prefix": output_prefix
            }
        )

        data = json.loads(result.content[0].text)
        if data.get('success'):
            print(f"  ✅ 捕获完成: {data.get('capture_file')}")
            print(f"  📊 统计: {data.get('statistics', {})}")
        else:
            print(f"  ❌ 捕获失败: {data.get('error')}")

    # 3. 停止监控模式
    print("\n🛑 停止监控模式...")
    await session.call_tool(
        "network_monitor",
        {"operation": "stop"}
    )

    print("\n✅ 抓包流程完成!")


# 使用示例
# await capture_workflow(session, channels=[1, 6, 11], duration=30)
```

---

## 故障排除

### 问题 1: MCP 服务无法启动

**症状**：Claude Desktop 显示工具不可用

**检查步骤**：

```bash
# 1. 测试配置文件
cd /path/to/kali-driver-mcp
cat config.yaml  # 确认配置正确

# 2. 测试 SSH 连接
ssh -i ~/.ssh/kali_vm kali@192.168.2.104  # 或使用密码

# 3. 手动启动服务测试
uv run python -m kali_driver_mcp.server --config config.yaml
# 应该显示: "MCP Server is running. Waiting for requests..."
# 按 Ctrl+C 停止

# 4. 查看日志
tail -f logs/kali-driver-mcp.log
```

**解决方案**：
- 确认 config.yaml 中的 VM IP 和认证信息正确
- 确认 Kali VM 正在运行且 SSH 可访问
- 检查共享文件夹是否正确挂载

---

### 问题 2: Claude Desktop 配置后不生效

**检查**：

```bash
# macOS/Linux
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 验证 JSON 格式
python3 -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**常见错误**：
- ❌ 使用了相对路径或 `~`
- ❌ JSON 格式错误（缺少逗号、引号等）
- ❌ `cwd` 路径不正确

**正确配置**：
```json
{
  "mcpServers": {
    "kali-driver": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "kali_driver_mcp.server",
        "--config",
        "/Users/haoyang/src/python/kali-driver-mcp/config.yaml"
      ],
      "cwd": "/Users/haoyang/src/python/kali-driver-mcp"
    }
  }
}
```

---

### 问题 3: SSH 连接失败

**症状**：日志显示 "SSH connection failed"

**检查**：

```bash
# 测试 SSH 连接
ssh kali@192.168.2.104

# 如果使用密钥
ssh -i ~/.ssh/kali_vm kali@192.168.2.104

# 检查密钥权限
chmod 600 ~/.ssh/kali_vm

# 检查 Kali VM SSH 配置
# 在 VM 中运行：
sudo systemctl status ssh
sudo cat /etc/ssh/sshd_config | grep PermitRootLogin
```

**解决方案**：
- 确认 VM IP 地址正确
- 确认 SSH 服务运行中
- 如果使用密钥，确认密钥已复制到 VM：
  ```bash
  ssh-copy-id -i ~/.ssh/kali_vm.pub kali@192.168.2.104
  ```

---

### 问题 4: 共享文件夹未挂载

**症状**：`code_sync` 工具返回 "not ready"

**检查（在 Kali VM 中）**：

```bash
# 查看挂载
mount | grep kali

# 查看目录
ls -la /home/kali/Desktop/share/

# VirtualBox: 安装增强功能
sudo apt install virtualbox-guest-utils virtualbox-guest-dkms

# 手动挂载（VirtualBox）
sudo mkdir -p /home/kali/Desktop/share
sudo mount -t vboxsf share_name /home/kali/Desktop/share
```

---

### 问题 5: 工具调用超时

**症状**：操作长时间无响应

**原因**：某些操作（如编译）可能需要较长时间

**解决方案**：
- 编译操作：正常可能需要 30-120 秒
- 数据包捕获：根据设置的 duration 参数
- 如果真的卡住，检查 SSH 连接是否断开

---

### 问题 6: Python 客户端导入错误

**症状**：`ModuleNotFoundError: No module named 'mcp'`

**解决**：

```bash
# 确认在正确的项目目录
cd /path/to/my-kali-automation

# 安装依赖
uv add mcp

# 或使用 pip
pip install mcp

# 运行
uv run python client.py
```

---

## 日志和调试

### 查看 MCP 服务日志

```bash
# 实时查看日志
tail -f /path/to/kali-driver-mcp/logs/kali-driver-mcp.log

# 查看最近的错误
grep ERROR /path/to/kali-driver-mcp/logs/kali-driver-mcp.log | tail -20

# 查看特定命令的执行
grep "CMD-" /path/to/kali-driver-mcp/logs/kali-driver-mcp.log
```

### 启用详细日志

修改 `config.yaml`:

```yaml
logging:
  level: "DEBUG"              # 改为 DEBUG
  enable_console: true        # 启用控制台输出
  log_commands: true          # 记录所有 SSH 命令
  log_tools: true             # 记录所有工具调用
```

### Claude Desktop 日志

**macOS**:
```bash
# Claude Desktop 日志位置
~/Library/Logs/Claude/
```

---

## 安全建议

1. **不要在生产环境使用密码认证**
   - 使用 SSH 密钥认证
   - 禁用密码登录

2. **限制 SSH 访问**
   ```bash
   # 在 Kali VM 的 /etc/ssh/sshd_config 中
   AllowUsers kali
   PermitRootLogin prohibit-password
   ```

3. **不要提交敏感配置**
   ```bash
   # 将 config.yaml 添加到 .gitignore
   echo "config.yaml" >> .gitignore
   ```

4. **使用防火墙**
   ```bash
   # 只允许本地网络访问 SSH
   sudo ufw allow from 192.168.0.0/16 to any port 22
   ```

---

## 更多资源

- **MCP 官方文档**: https://modelcontextprotocol.io
- **项目 README**: [README.md](README.md)
- **工具参考**: [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)
- **测试指南**: [TEST_RESULTS.md](TEST_RESULTS.md)
- **日志指南**: [LOGGING_GUIDE.md](LOGGING_GUIDE.md)

---

## 总结

本指南涵盖了三种连接 MCP 服务的方式：

1. **Claude Desktop** - 最简单，适合日常使用
2. **Python 客户端** - 灵活，适合自动化
3. **其他工具** - 集成到现有工作流

选择最适合你需求的方式开始使用吧！

如有问题，请查看 [故障排除](#故障排除) 部分或提交 Issue。
