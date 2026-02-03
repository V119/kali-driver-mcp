# MCP 工具快速参考

## 📋 9 个可用工具速查

### 1️⃣ kernel_info - 内核信息

**功能**：获取 Kali VM 内核版本和配置

**Claude Desktop**：
```
请查看 Kali VM 的内核版本
```

**Python**：
```python
result = await client.call_tool("kernel_info", {"detail_level": "basic"})
# 返回: {"version": "...", "architecture": "...", ...}
```

---

### 2️⃣ file_ops - 文件操作

**功能**：列出、读取、搜索共享文件夹中的文件

**Claude Desktop**：
```
列出共享文件夹中的所有 .c 文件
显示 driver.c 的内容
搜索包含 "init_module" 的文件
```

**Python**：
```python
# 列出文件
result = await client.call_tool("file_ops", {
    "operation": "list",
    "filter_pattern": "*.c",
    "recursive": True
})

# 读取文件
result = await client.call_tool("file_ops", {
    "operation": "read",
    "path": "driver.c"
})

# 搜索内容
result = await client.call_tool("file_ops", {
    "operation": "search",
    "search_pattern": "init_module"
})
```

---

### 3️⃣ code_sync - 共享文件夹验证

**功能**：检查共享文件夹是否正确挂载

**Claude Desktop**：
```
验证共享文件夹是否可访问
```

**Python**：
```python
result = await client.call_tool("code_sync", {})
# 返回: {"ready": true, "vm_path": "/path/...", ...}
```

---

### 4️⃣ driver_compile - 编译驱动

**功能**：使用 make 编译内核驱动

**Claude Desktop**：
```
编译驱动
清理并重新编译驱动，显示详细输出
```

**Python**：
```python
# 普通编译
result = await client.call_tool("driver_compile", {
    "clean": False,
    "verbose": False
})

# 清理编译（详细输出）
result = await client.call_tool("driver_compile", {
    "clean": True,
    "verbose": True
})

# 指定目标
result = await client.call_tool("driver_compile", {
    "target": "modules",
    "clean": True
})
```

---

### 5️⃣ driver_load - 驱动加载/卸载

**功能**：加载、卸载、重载内核模块

**Claude Desktop**：
```
加载驱动 mydriver，设置 debug=1
卸载驱动 mydriver
重新加载驱动 mydriver
查看已加载的驱动列表
查看 mydriver 的详细信息
```

**Python**：
```python
# 加载驱动
result = await client.call_tool("driver_load", {
    "operation": "load",
    "module_name": "mydriver",
    "parameters": {
        "debug": "1",
        "mode": "test"
    }
})

# 卸载驱动
result = await client.call_tool("driver_load", {
    "operation": "unload",
    "module_name": "mydriver",
    "force": False
})

# 重载驱动
result = await client.call_tool("driver_load", {
    "operation": "reload",
    "module_name": "mydriver"
})

# 列出所有已加载模块
result = await client.call_tool("driver_load", {
    "operation": "list"
})

# 查看模块信息
result = await client.call_tool("driver_load", {
    "operation": "info",
    "module_name": "mydriver"
})
```

---

### 6️⃣ log_viewer - 日志查看

**功能**：查看内核日志（dmesg）和系统日志

**Claude Desktop**：
```
查看最近 50 行 dmesg 日志
查看包含 "mydriver" 的内核日志
查看最近 5 分钟的系统日志
```

**Python**：
```python
# 查看 dmesg 日志
result = await client.call_tool("log_viewer", {
    "source": "dmesg",
    "lines": 50
})

# 过滤特定内容
result = await client.call_tool("log_viewer", {
    "source": "dmesg",
    "lines": 100,
    "filter_pattern": "mydriver"
})

# 按日志级别过滤
result = await client.call_tool("log_viewer", {
    "source": "kern",
    "level": "error",
    "lines": 50
})

# 时间过滤
result = await client.call_tool("log_viewer", {
    "source": "journal",
    "since": "5 min ago",
    "filter_pattern": "driver"
})
```

**日志源选项**：
- `dmesg` - 内核环缓冲区
- `syslog` - 系统日志
- `kern` - 内核日志（/var/log/kern.log）
- `journal` - systemd 日志

---

### 7️⃣ network_info - 网络接口信息

**功能**：查询网络接口配置和统计信息

**Claude Desktop**：
```
显示所有网络接口
显示 wlan0 的详细信息
显示 wlan0 的统计信息
显示 wlan0 的驱动信息
```

**Python**：
```python
# 所有接口（基本信息）
result = await client.call_tool("network_info", {
    "interface": "all",
    "detail_level": "basic"
})

# 特定接口（详细信息）
result = await client.call_tool("network_info", {
    "interface": "wlan0",
    "detail_level": "detailed"
})

# 统计信息
result = await client.call_tool("network_info", {
    "interface": "wlan0",
    "detail_level": "statistics"
})

# 驱动信息
result = await client.call_tool("network_info", {
    "interface": "wlan0",
    "info_type": "driver"
})
```

**detail_level 选项**：
- `basic` - 基本状态（IP、MAC、状态）
- `detailed` - 详细配置
- `statistics` - 流量统计

**info_type 选项**：
- `status` - 接口状态
- `driver` - 驱动信息
- `settings` - 无线设置
- `stats` - 统计数据

---

### 8️⃣ network_monitor - 监控模式管理

**功能**：启动/停止无线网卡监控模式（airmon-ng）

**Claude Desktop**：
```
启动监控模式，使用频道 6
停止监控模式
查看监控模式状态
```

**Python**：
```python
# 启动监控模式
result = await client.call_tool("network_monitor", {
    "operation": "start",
    "channel": 6
})

# 停止监控模式
result = await client.call_tool("network_monitor", {
    "operation": "stop"
})

# 查看状态
result = await client.call_tool("network_monitor", {
    "operation": "status"
})
```

**注意**：
- 启动监控模式会自动关闭干扰进程（NetworkManager 等）
- 停止监控模式会恢复正常模式
- 频道范围：1-165（2.4GHz: 1-14, 5GHz: 36-165）

---

### 9️⃣ packet_capture - 数据包捕获

**功能**：使用 airodump-ng 捕获无线数据包

**Claude Desktop**：
```
在频道 6 捕获数据包 60 秒
捕获 BSSID 为 AA:BB:CC:DD:EE:FF 的 AP 数据包 120 秒
```

**Python**：
```python
# 基本捕获
result = await client.call_tool("packet_capture", {
    "channel": 6,
    "duration": 60,
    "output_prefix": "capture"
})

# 捕获特定 AP
result = await client.call_tool("packet_capture", {
    "channel": 6,
    "bssid": "AA:BB:CC:DD:EE:FF",
    "duration": 120,
    "output_prefix": "target_ap"
})

# 返回结果包含
# {
#   "success": true,
#   "capture_file": "/tmp/captures/capture-01.cap",
#   "csv_file": "/tmp/captures/capture-01.csv",
#   "statistics": {
#     "access_points": 5,
#     "clients": 12,
#     "packets": 1234
#   }
# }
```

**参数说明**：
- `channel` - 监听频道（可选，默认使用当前频道）
- `bssid` - 目标 AP 的 MAC 地址（可选）
- `duration` - 捕获时长（秒），1-3600
- `output_prefix` - 输出文件名前缀

---

## 🔄 常见工作流

### 工作流 1: 驱动开发调试

```python
# 1. 验证环境
await client.call_tool("code_sync", {})
await client.call_tool("kernel_info", {"detail_level": "basic"})

# 2. 编译驱动
await client.call_tool("driver_compile", {"clean": True, "verbose": True})

# 3. 加载驱动
await client.call_tool("driver_load", {
    "operation": "load",
    "module_name": "mydriver",
    "parameters": {"debug": "1"}
})

# 4. 检查日志
await client.call_tool("log_viewer", {
    "source": "dmesg",
    "lines": 50,
    "filter_pattern": "mydriver"
})

# 5. 测试网络接口
await client.call_tool("network_info", {
    "interface": "wlan0",
    "detail_level": "detailed"
})
```

### 工作流 2: 无线抓包分析

```python
# 1. 检查网络接口
await client.call_tool("network_info", {"interface": "wlan0"})

# 2. 启动监控模式
await client.call_tool("network_monitor", {
    "operation": "start",
    "channel": 6
})

# 3. 捕获数据包
await client.call_tool("packet_capture", {
    "channel": 6,
    "duration": 120,
    "output_prefix": "scan"
})

# 4. 停止监控模式
await client.call_tool("network_monitor", {"operation": "stop"})

# 5. 查看捕获日志
await client.call_tool("log_viewer", {
    "source": "dmesg",
    "filter_pattern": "airodump"
})
```

### 工作流 3: 驱动参数测试

```python
# 测试不同参数组合
test_params = [
    {"debug": "0", "mode": "normal"},
    {"debug": "1", "mode": "normal"},
    {"debug": "1", "mode": "test"},
]

for params in test_params:
    # 卸载旧驱动
    await client.call_tool("driver_load", {
        "operation": "unload",
        "module_name": "mydriver",
        "force": True
    })

    # 加载新参数
    await client.call_tool("driver_load", {
        "operation": "load",
        "module_name": "mydriver",
        "parameters": params
    })

    # 等待并检查日志
    await asyncio.sleep(2)
    result = await client.call_tool("log_viewer", {
        "source": "dmesg",
        "lines": 20,
        "filter_pattern": "mydriver"
    })

    # 分析结果...
```

---

## 💡 使用技巧

### 1. Claude Desktop 自然语言提示词

**推荐的对话方式**：

```
❌ 不好：执行 driver_compile
✅ 好的：请帮我编译驱动

❌ 不好：调用 kernel_info 工具
✅ 好的：查看一下内核版本

❌ 不好：用 log_viewer 看 dmesg
✅ 好的：检查最近的内核日志，看看驱动是否正常加载
```

Claude 会自动理解你的意图并调用相应的工具。

### 2. Python 客户端错误处理

```python
try:
    result = await client.call_tool("driver_load", {
        "operation": "load",
        "module_name": "mydriver"
    })

    if not result.get("success"):
        print(f"加载失败: {result.get('error')}")
        # 查看详细日志
        log_result = await client.call_tool("log_viewer", {
            "source": "dmesg",
            "lines": 30
        })
except Exception as e:
    print(f"工具调用异常: {e}")
```

### 3. 日志过滤技巧

**过滤特定模块的错误**：
```python
await client.call_tool("log_viewer", {
    "source": "dmesg",
    "filter_pattern": "mydriver.*error|mydriver.*fail"
})
```

**查看最近的编译输出**：
```python
result = await client.call_tool("driver_compile", {"verbose": True})
build_output = result.get("build_output", "")
# 分析编译警告和错误...
```

### 4. 组合工具使用

**智能驱动重载**：
```python
async def smart_reload(client, module_name, params=None):
    """智能重载：先卸载，编译，再加载."""

    # 1. 卸载（忽略错误）
    await client.call_tool("driver_load", {
        "operation": "unload",
        "module_name": module_name,
        "force": True
    })

    # 2. 编译
    compile_result = await client.call_tool("driver_compile", {
        "clean": False,
        "verbose": False
    })

    if not compile_result.get("success"):
        return {"success": False, "stage": "compile", "error": compile_result}

    # 3. 加载
    load_result = await client.call_tool("driver_load", {
        "operation": "load",
        "module_name": module_name,
        "parameters": params or {}
    })

    return load_result
```

---

## 🔧 返回值格式

所有工具返回 JSON 格式，通常包含：

```json
{
  "success": true,           // 操作是否成功
  "error": null,            // 错误信息（如果失败）
  // ... 其他工具特定的字段
}
```

**示例返回值**：

**kernel_info**：
```json
{
  "version": "6.1.0-kali5-amd64",
  "architecture": "x86_64",
  "release": "6.1.0-kali5-amd64",
  "build_date": "2023-02-23"
}
```

**driver_compile**：
```json
{
  "success": true,
  "build_time": 12.345,
  "warnings": 2,
  "errors": 0,
  "build_output": "make -C /lib/modules/..."
}
```

**driver_load** (load)：
```json
{
  "success": true,
  "operation": "load",
  "module_name": "mydriver",
  "parameters": {"debug": "1"},
  "load_output": "Module loaded successfully"
}
```

**network_info**：
```json
{
  "interfaces": [
    {
      "name": "wlan0",
      "state": "UP",
      "mac": "AA:BB:CC:DD:EE:FF",
      "ip": "192.168.1.100",
      "driver": "ath9k"
    }
  ]
}
```

**packet_capture**：
```json
{
  "success": true,
  "capture_file": "/tmp/captures/scan-01.cap",
  "csv_file": "/tmp/captures/scan-01.csv",
  "statistics": {
    "access_points": 15,
    "clients": 42,
    "packets": 12345,
    "data_packets": 8901
  }
}
```

---

## 📚 相关文档

- **[MCP 客户端使用指南](MCP_CLIENT_GUIDE.md)** - 详细的连接和使用步骤
- **[Python 客户端示例](mcp_client_example.py)** - 完整的可运行示例
- **[README.md](README.md)** - 项目总览和安装指南
- **[测试指南](TEST_RESULTS.md)** - 测试用例和结果
- **[日志指南](LOGGING_GUIDE.md)** - 日志系统使用

---

**更新时间**: 2026-02-03
