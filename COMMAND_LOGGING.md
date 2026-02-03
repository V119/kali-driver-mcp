# 命令输入输出日志记录 - 修改说明

## ✅ 修改内容

### 修改文件
- `src/kali_driver_mcp/logging_config.py`

### 修改的函数
1. **`log_command_start()`** - 记录命令输入
2. **`log_command_end()`** - 记录命令输出和错误输出

## 新的日志格式

### 1. 命令开始（输入）
```log
2026-02-03 20:08:29 - ssh_commands - INFO - log_command_start:83 - [CMD-1] Starting command: uname -a
```

**特点**：
- 显示完整命令（前200字符在主日志行）
- 如果命令超过200字符，会额外单独记录完整命令
- 包含命令ID `[CMD-1]` 用于关联开始和结束

### 2. 命令完成（状态）
```log
2026-02-03 20:08:29 - ssh_commands - INFO - log_command_end:130 - [CMD-1] Completed with exit code 0 in 0.054s
```

**特点**：
- 显示退出码（0表示成功）
- 显示执行耗时
- 成功命令用 INFO 级别，失败命令用 WARNING 级别

### 3. 标准输出（STDOUT）
```log
2026-02-03 20:08:29 - ssh_commands - INFO - log_command_end:140 - [CMD-1] STDOUT:
Linux kali 6.18.5+kali-arm64 #1 SMP PREEMPT Kali 6.18.5-1kali1 (2026-01-19) aarch64 GNU/Linux
```

**特点**：
- ✅ **始终记录**（只要有输出）
- 显示完整输出（前500字符）
- 如果超过500字符，会显示 `... (truncated)`
- 使用 INFO 级别

### 4. 错误输出（STDERR）
```log
2026-02-03 20:09:12 - ssh_commands - WARNING - log_command_end:148 - [CMD-1] STDERR:
cat: /nonexistent_file: No such file or directory
```

**特点**：
- ✅ **始终记录**（只要有错误输出）
- 显示完整错误输出（前500字符）
- 如果超过500字符，会显示 `... (truncated)`
- 使用 **WARNING 级别**（更醒目，便于查找错误）

## 实际示例

### 示例1: 成功的命令

**日志记录**：
```log
2026-02-03 20:08:29 - ssh_commands - INFO - log_command_start:83 - [CMD-1] Starting command: uname -a
2026-02-03 20:08:29 - kali_driver_mcp.ssh_manager - DEBUG - execute:125 - Executing command: uname -a
2026-02-03 20:08:29 - kali_driver_mcp.ssh_manager - DEBUG - execute:144 - Command exit code: 0, stdout length: 93, stderr length: 0
2026-02-03 20:08:29 - ssh_commands - INFO - log_command_end:130 - [CMD-1] Completed with exit code 0 in 0.054s
2026-02-03 20:08:29 - ssh_commands - INFO - log_command_end:140 - [CMD-1] STDOUT:
Linux kali 6.18.5+kali-arm64 #1 SMP PREEMPT Kali 6.18.5-1kali1 (2026-01-19) aarch64 GNU/Linux
```

**包含信息**：
- ✅ 命令本身：`uname -a`
- ✅ 退出码：`0`
- ✅ 执行时间：`0.054s`
- ✅ 输出长度：`93 bytes`
- ✅ 完整输出：`Linux kali ...`

### 示例2: 失败的命令

**日志记录**：
```log
2026-02-03 20:09:12 - ssh_commands - INFO - log_command_start:83 - [CMD-1] Starting command: cat /nonexistent_file
2026-02-03 20:09:12 - kali_driver_mcp.ssh_manager - DEBUG - execute:125 - Executing command: cat /nonexistent_file
2026-02-03 20:09:12 - kali_driver_mcp.ssh_manager - DEBUG - execute:144 - Command exit code: 1, stdout length: 0, stderr length: 48
2026-02-03 20:09:12 - ssh_commands - WARNING - log_command_end:130 - [CMD-1] Completed with exit code 1 in 0.030s
2026-02-03 20:09:12 - ssh_commands - WARNING - log_command_end:148 - [CMD-1] STDERR:
cat: /nonexistent_file: No such file or directory
```

**包含信息**：
- ✅ 命令本身：`cat /nonexistent_file`
- ✅ 退出码：`1`（非零表示失败）
- ✅ 执行时间：`0.030s`
- ✅ 错误输出长度：`48 bytes`
- ✅ 完整错误信息：`cat: /nonexistent_file: No such file or directory`
- ⚠️ 使用 WARNING 级别（更容易查找）

### 示例3: 有输出和错误的命令

**日志记录**：
```log
2026-02-03 20:10:00 - ssh_commands - INFO - log_command_start:83 - [CMD-3] Starting command: make
2026-02-03 20:10:05 - ssh_commands - WARNING - log_command_end:130 - [CMD-3] Completed with exit code 2 in 4.532s
2026-02-03 20:10:05 - ssh_commands - INFO - log_command_end:140 - [CMD-3] STDOUT:
gcc -o myapp main.c
Linking...
2026-02-03 20:10:05 - ssh_commands - WARNING - log_command_end:148 - [CMD-3] STDERR:
main.c:42: error: undefined reference to 'missing_function'
make: *** [Makefile:10: myapp] Error 1
```

**包含信息**：
- ✅ 同时包含标准输出和错误输出
- ✅ 可以看到编译过程和错误信息

## 如何查看日志

### 查看所有命令执行
```bash
# 查看命令输入
grep "Starting command" logs/kali-driver-mcp.log

# 查看命令输出
grep -A 2 "STDOUT" logs/kali-driver-mcp.log

# 查看错误输出
grep -A 2 "STDERR" logs/kali-driver-mcp.log
```

### 查看特定命令的完整记录
```bash
# 查看命令ID为1的所有日志
grep "CMD-1" logs/kali-driver-mcp.log
```

### 查看失败的命令
```bash
# 查看所有非零退出码
grep "exit code [^0]" logs/kali-driver-mcp.log

# 查看所有 WARNING 级别的命令完成记录（表示失败）
grep "WARNING.*Completed with exit code" logs/kali-driver-mcp.log
```

### 实时监控命令执行
```bash
# 监控所有命令
tail -f logs/kali-driver-mcp.log | grep --line-buffered "CMD-\|STDOUT\|STDERR"

# 只监控错误
tail -f logs/kali-driver-mcp.log | grep --line-buffered "STDERR\|WARNING"
```

## 日志级别说明

### 不同场景的日志级别

| 场景 | 日志级别 | 说明 |
|------|---------|------|
| 命令开始 | INFO | 记录要执行的命令 |
| 命令成功完成 | INFO | 退出码为0 |
| 命令失败完成 | WARNING | 退出码非0 |
| 标准输出 | INFO | 正常输出 |
| 错误输出 | WARNING | 更醒目，便于查找问题 |
| 详细执行信息 | DEBUG | 包含输出长度等详细信息 |

### 控制台显示级别

```bash
# 只看 WARNING 及以上（失败的命令）
pytest -v --log-cli-level=WARNING

# 看 INFO 及以上（所有命令和输出）
pytest -v --log-cli-level=INFO

# 看所有日志（包括 DEBUG）
pytest -v --log-cli-level=DEBUG
```

## 输出截断说明

为了避免日志文件过大，长输出会被截断：

### STDOUT/STDERR 截断规则
- **前 500 字符**：完整显示
- **超过 500 字符**：显示前500字符 + `... (truncated)`
- **完整输出**：仍然保存在 log_data 中（用于 JSON 格式）

### 长命令截断规则
- **前 200 字符**：在主日志行显示
- **超过 200 字符**：额外单独记录完整命令

### 如果需要完整输出

**方法1: 使用 JSON 格式日志**
```python
setup_logging(
    log_level="DEBUG",
    log_file="logs/kali-driver-mcp.json",
    json_format=True,  # 启用 JSON 格式
    enable_console=False
)
```

JSON 格式日志包含完整的 stdout 和 stderr（不截断）。

**方法2: 修改截断长度**

在 `logging_config.py` 中修改：
```python
# STDOUT
stdout_preview = stdout[:1000] if len(stdout) > 1000 else stdout  # 改为1000字符

# 命令
command_preview = command[:500] if len(command) > 500 else command  # 改为500字符
```

## 与 pytest 日志的关系

### 文件日志
- **应用日志**：`logs/kali-driver-mcp.log` - 包含所有命令输入输出
- **pytest 日志**：`logs/pytest.log` - pytest 框架自己的日志

### 控制台日志
- **pytest 控制台**：显示测试结果和指定级别的日志
- **应用日志**：由 `log_cli_level` 控制显示级别

### 推荐配置

**调试时**：
```bash
pytest -v --log-cli-level=INFO  # 看所有命令和输出
```

**正常运行**：
```bash
pytest -v --log-cli-level=WARNING  # 只看失败的命令
```

**静默模式**：
```bash
pytest -v --log-cli-level=CRITICAL  # 不显示日志，只看文件
```

## 总结

✅ **修改后的优势**：

1. **完整记录**：命令输入、输出、错误输出都记录
2. **易于追踪**：使用命令ID关联开始和结束
3. **清晰明了**：STDOUT/STDERR 明确标记
4. **便于调试**：失败命令用 WARNING 级别，容易查找
5. **追加模式**：日志不会被覆盖，可以查看历史
6. **智能截断**：避免日志过大，同时保留关键信息

---

**修改时间**: 2026-02-03
**状态**: ✅ 已完成并测试通过
