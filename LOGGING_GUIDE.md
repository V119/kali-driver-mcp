# 测试日志使用指南

## ✅ 已修复的问题

### 1. ✅ 日志追加模式
- **问题**: 日志文件会被覆盖
- **修复**:
  - `pytest.ini`: 添加 `log_file_mode = a`
  - `logging_config.py`: FileHandler 使用 `mode='a'`

### 2. ✅ 代码日志记录
- **问题**: 代码中的日志没有记录到文件
- **修复**: 在 `tests/conftest.py` 添加自动日志初始化 fixture

## 日志文件位置

### 应用程序日志（详细）
```
logs/kali-driver-mcp.log
```
- 包含所有 DEBUG 级别的日志
- **追加模式**，不会覆盖
- 包含代码中所有 logger 输出

### pytest 日志（测试框架）
```
logs/pytest.log
```
- pytest 框架自己的日志
- **追加模式**，不会覆盖

## 查看日志的方法

### 1. 实时查看（推荐用于调试）
```bash
# 在一个终端中实时监控日志
tail -f logs/kali-driver-mcp.log

# 在另一个终端运行测试
python3 -m pytest tests/integration/test_ssh_connection.py -v
```

### 2. 查看最近的日志
```bash
# 查看最后50行
tail -50 logs/kali-driver-mcp.log

# 查看最后100行
tail -100 logs/kali-driver-mcp.log
```

### 3. 搜索特定内容
```bash
# 搜索所有命令执行记录
grep "CMD-" logs/kali-driver-mcp.log

# 搜索错误
grep "ERROR" logs/kali-driver-mcp.log

# 搜索特定工具调用
grep "TOOL-" logs/kali-driver-mcp.log

# 搜索特定命令
grep "insmod" logs/kali-driver-mcp.log
```

### 4. 按时间范围查看
```bash
# 查看某个时间段的日志
grep "2026-02-03 20:0" logs/kali-driver-mcp.log

# 查看最近5分钟的日志
tail -1000 logs/kali-driver-mcp.log | grep "$(date '+%Y-%m-%d %H:%M')"
```

## 控制台日志输出

### 默认行为（显示 INFO 及以上级别）
```bash
python3 -m pytest tests/unit/test_tools.py -v
```

输出示例：
```
2026-02-03 20:02:28 [INFO] kali_driver_mcp.ssh_manager: Connecting to 192.168.2.104:22
2026-02-03 20:02:28 [INFO] ssh_commands: [CMD-1] Starting command: echo 'test'
2026-02-03 20:02:28 [INFO] ssh_commands: [CMD-1] Completed with exit code 0 in 0.037s
```

### 显示 DEBUG 级别日志
```bash
python3 -m pytest tests/unit/test_tools.py -v --log-cli-level=DEBUG
```

### 只显示 WARNING 及以上（更简洁）
```bash
python3 -m pytest tests/unit/test_tools.py -v --log-cli-level=WARNING
```

### 完全禁用控制台日志
```bash
python3 -m pytest tests/unit/test_tools.py -v --log-cli-level=CRITICAL
```

## 日志级别说明

日志按严重程度从低到高：

1. **DEBUG**: 详细的调试信息（所有 SSH 协议细节）
2. **INFO**: 一般信息（命令执行、工具调用）
3. **WARNING**: 警告信息（非致命错误）
4. **ERROR**: 错误信息（操作失败）
5. **CRITICAL**: 严重错误（系统级问题）

## 日志内容说明

### 命令执行日志
```
2026-02-03 20:02:28 - ssh_commands - INFO - log_command_start:79 - [CMD-1] Starting command: echo 'test'
2026-02-03 20:02:28 - ssh_commands - INFO - log_command_end:120 - [CMD-1] Completed with exit code 0 in 0.037s
```

- `[CMD-1]`: 命令ID，用于关联开始和结束
- 包含执行时间、退出码

### SSH 连接日志
```
2026-02-03 20:02:28 - kali_driver_mcp.ssh_manager - INFO - connect:52 - Connecting to 192.168.2.104:22
2026-02-03 20:02:28 - kali_driver_mcp.ssh_manager - INFO - connect:71 - SSH connection established
```

### 工具调用日志
```
2026-02-03 20:02:28 - mcp_tools - INFO - log_tool_start:174 - [TOOL-1] Invoking tool: kernel_info
2026-02-03 20:02:30 - mcp_tools - INFO - log_tool_end:216 - [TOOL-1] Tool kernel_info completed in 1.234s
```

## 日志管理

### 清理旧日志
```bash
# 清空日志文件
> logs/kali-driver-mcp.log

# 或者删除后自动重建
rm logs/kali-driver-mcp.log
# 下次运行测试时会自动创建
```

### 日志轮转（可选）
如果日志文件太大，可以手动归档：

```bash
# 归档当前日志
mv logs/kali-driver-mcp.log logs/kali-driver-mcp-$(date +%Y%m%d).log

# 压缩归档
gzip logs/kali-driver-mcp-*.log
```

## 实际使用示例

### 示例1: 调试测试失败
```bash
# 1. 清空旧日志
> logs/kali-driver-mcp.log

# 2. 运行失败的测试，显示所有日志
python3 -m pytest tests/integration/test_tools_integration.py::TestKernelInfoIntegration::test_get_kernel_info -v --log-cli-level=DEBUG

# 3. 如果测试失败，查看详细日志
cat logs/kali-driver-mcp.log | grep -A 5 -B 5 ERROR
```

### 示例2: 监控集成测试
```bash
# 终端1: 监控日志
tail -f logs/kali-driver-mcp.log | grep --line-buffered "CMD-\|TOOL-\|ERROR"

# 终端2: 运行测试
python3 -m pytest tests/integration -v
```

### 示例3: 查看特定测试的命令执行
```bash
# 运行测试
python3 -m pytest tests/integration/test_ssh_connection.py::TestSSHConnection::test_execute_whoami -v

# 查看执行的命令
grep "Starting command" logs/kali-driver-mcp.log | tail -5

# 查看命令结果
grep "Completed with exit code" logs/kali-driver-mcp.log | tail -5
```

## 配置文件

### pytest.ini 日志配置
```ini
# 控制台日志
log_cli = true
log_cli_level = INFO

# 文件日志（追加模式）
log_file = logs/pytest.log
log_file_level = DEBUG
log_file_mode = a
```

### conftest.py 应用日志配置
```python
@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Configure logging for all tests - runs automatically."""
    setup_logging(
        log_level="DEBUG",
        log_file="logs/kali-driver-mcp.log",
        json_format=False,
        enable_console=False
    )
```

## 常见问题

### Q: 为什么看不到日志？
A: 确保：
1. 使用 `-v` 参数运行 pytest
2. 检查 `log_cli_level` 设置（默认 INFO）
3. 查看 `logs/kali-driver-mcp.log` 文件

### Q: 如何只看我的代码日志，不看 asyncssh 的？
A: 使用 grep 过滤：
```bash
tail -f logs/kali-driver-mcp.log | grep -v "asyncssh"
```

### Q: 日志太多了，如何简化？
A: 方法1: 提高日志级别
```bash
pytest tests/unit -v --log-cli-level=WARNING
```

方法2: 只看关键信息
```bash
tail -f logs/kali-driver-mcp.log | grep "CMD-\|TOOL-\|ERROR"
```

### Q: 如何在测试代码中添加自己的日志？
A: 使用 Python logging：
```python
import logging

logger = logging.getLogger(__name__)

def my_test():
    logger.info("开始测试")
    logger.debug("详细信息: value=%s", some_value)
    logger.error("发生错误: %s", error_msg)
```

---

**更新时间**: 2026-02-03
**状态**: ✅ 所有日志功能正常工作
