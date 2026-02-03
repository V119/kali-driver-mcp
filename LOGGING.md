# Logging Guide

This document explains the comprehensive logging system in Kali Driver MCP Server.

## Overview

The MCP server includes a detailed logging system that records:
- Every SSH command executed (input, output, duration, exit code)
- Every MCP tool invocation (arguments, results, duration)
- All errors and exceptions with full stack traces
- Connection events and state changes

## Configuration

Configure logging in `config.yaml`:

```yaml
logging:
  # Log viewer settings (for viewing VM logs)
  max_lines: 1000
  default_source: "dmesg"

  # Logging system configuration
  level: "INFO"                    # DEBUG, INFO, WARNING, ERROR
  file: "logs/kali-driver-mcp.log" # Log file path (null to disable)
  json_format: false               # Use JSON for structured logging
  enable_console: true             # Log to stderr
  log_commands: true               # Log all SSH commands
  log_tools: true                  # Log all MCP tool calls
```

## Log Levels

- **DEBUG**: Detailed information for diagnosing problems
  - All command input/output
  - Internal state changes
  - Detailed execution flow

- **INFO**: General informational messages
  - Tool invocations
  - Command execution summaries
  - Connection events

- **WARNING**: Warning messages
  - Non-zero exit codes
  - Timeouts
  - Recoverable errors

- **ERROR**: Error messages
  - Failed commands
  - Tool execution failures
  - Connection errors

## Log Formats

### Text Format (Default)

Human-readable format:
```
2024-01-01 12:00:00 - ssh_commands - INFO - [CMD-1] Starting command: uname -r
2024-01-01 12:00:01 - ssh_commands - INFO - [CMD-1] Completed with exit code 0 in 0.123s
```

### JSON Format

Structured format for log aggregation tools:
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "logger": "ssh_commands",
  "message": "[CMD-1] Starting command: uname -r",
  "extra": {
    "cmd_id": 1,
    "command": "uname -r",
    "timeout": 30
  }
}
```

## Command Logging

When `log_commands: true`, every SSH command is logged with:

**Start:**
```
[CMD-1] Starting command: ls /mnt/kali-share
  cmd_id: 1
  command: ls /mnt/kali-share
  timeout: 30
  started_at: 2024-01-01T12:00:00
```

**Completion:**
```
[CMD-1] Completed with exit code 0 in 0.123s
  cmd_id: 1
  exit_code: 0
  stdout_length: 1234
  stderr_length: 0
  duration_seconds: 0.123
  completed_at: 2024-01-01T12:00:01
```

**At DEBUG level, full output is logged:**
```
  stdout: "file1.c\nfile2.c\nMakefile\n..."
  stderr: ""
```

## Tool Logging

When `log_tools: true`, every MCP tool call is logged with:

**Start:**
```
[TOOL-1] Invoking tool: kernel_info
  tool_id: 1
  tool_name: kernel_info
  arguments: {"detail_level": "basic"}
  started_at: 2024-01-01T12:00:00
```

**Completion:**
```
[TOOL-1] Tool kernel_info completed in 1.234s
  tool_id: 1
  tool_name: kernel_info
  duration_seconds: 1.234
  success: true
  result_keys: ["version", "architecture"]
```

**On Error:**
```
[TOOL-1] Tool kernel_info failed: Connection timeout
  tool_id: 1
  tool_name: kernel_info
  error_type: TimeoutError
  error_message: Connection timeout
  [Full stack trace]
```

## Log Files

By default, logs are written to:
- **Console (stderr)**: INFO level and above
- **Log file**: DEBUG level and above (all details)

Log file location: `logs/kali-driver-mcp.log`

### Log Rotation

The logging system does not include built-in rotation. Use logrotate:

```bash
# /etc/logrotate.d/kali-driver-mcp
/path/to/kali-driver-mcp/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 user group
}
```

## Analyzing Logs

Use the included `analyze_logs.py` tool:

```bash
# Show statistics
python analyze_logs.py logs/kali-driver-mcp.log --stats

# Extract all SSH commands
python analyze_logs.py logs/kali-driver-mcp.log --commands

# Extract all tool invocations
python analyze_logs.py logs/kali-driver-mcp.log --tools

# Show only errors
python analyze_logs.py logs/kali-driver-mcp.log --errors

# Save to JSON file
python analyze_logs.py logs/kali-driver-mcp.log --commands --output commands.json
```

### Example Output

```
=== Log Statistics ===

Total Lines: 1523
Commands: 42
Tools: 15
Errors: 2
Warnings: 5

By Level:
  DEBUG: 856
  INFO: 612
  WARNING: 5
  ERROR: 2
```

## Debugging Workflows

### 1. Tool Not Working

```bash
# Find the specific tool call
python analyze_logs.py logs/kali-driver-mcp.log --tools | grep "tool_name"

# Check for errors
python analyze_logs.py logs/kali-driver-mcp.log --errors

# Review all commands executed by that tool
# (correlate by timestamp)
```

### 2. SSH Command Failing

```bash
# Find all failed commands (exit_code != 0)
grep "exit code [1-9]" logs/kali-driver-mcp.log

# Get full command details (enable DEBUG level)
# Edit config.yaml: level: "DEBUG"
# Restart server and retry
```

### 3. Performance Issues

```bash
# Find slow operations
grep "duration_seconds" logs/kali-driver-mcp.log | sort -t: -k2 -n

# Check for timeouts
grep -i timeout logs/kali-driver-mcp.log
```

## Best Practices

1. **Development**: Use `DEBUG` level with file logging
   ```yaml
   level: "DEBUG"
   file: "logs/dev.log"
   ```

2. **Production**: Use `INFO` level with JSON format
   ```yaml
   level: "INFO"
   json_format: true
   file: "logs/prod.log"
   ```

3. **Troubleshooting**: Enable DEBUG for specific components
   ```python
   # In code or via logging config
   logging.getLogger("ssh_commands").setLevel(logging.DEBUG)
   ```

4. **Log Aggregation**: Use JSON format for ELK, Splunk, etc.
   ```yaml
   json_format: true
   ```

5. **Disk Space**: Monitor log file size
   ```bash
   du -h logs/
   # Set up logrotate
   ```

## Log Examples

### Successful Driver Compilation

```
2024-01-01 12:00:00 - mcp_tools - INFO - [TOOL-1] Invoking tool: driver_compile
2024-01-01 12:00:00 - ssh_commands - INFO - [CMD-1] Starting command: cd /mnt/kali-share && make -j4
2024-01-01 12:00:05 - ssh_commands - INFO - [CMD-1] Completed with exit code 0 in 5.234s
2024-01-01 12:00:05 - mcp_tools - INFO - [TOOL-1] Tool driver_compile completed in 5.456s
```

### Failed Driver Load

```
2024-01-01 12:01:00 - mcp_tools - INFO - [TOOL-2] Invoking tool: driver_load
2024-01-01 12:01:00 - ssh_commands - INFO - [CMD-2] Starting command: insmod /mnt/kali-share/mydriver.ko
2024-01-01 12:01:01 - ssh_commands - WARNING - [CMD-2] Completed with exit code 1 in 0.123s
2024-01-01 12:01:01 - ssh_commands - DEBUG - [CMD-2] stderr: insmod: ERROR: could not insert module: Invalid module format
2024-01-01 12:01:01 - mcp_tools - INFO - [TOOL-2] Tool driver_load completed in 0.234s
```

### Connection Error

```
2024-01-01 12:02:00 - kali_driver_mcp.ssh_manager - ERROR - Failed to connect to VM: Connection refused
2024-01-01 12:02:00 - mcp_tools - ERROR - [TOOL-3] Tool kernel_info failed: Connection refused
  Traceback (most recent call last):
    ...
  SSHConnectionError: Failed to connect to VM: Connection refused
```

## Privacy & Security

- **Never log sensitive data** (passwords are not logged)
- SSH key paths are logged but not key contents
- Command arguments may contain sensitive info - review before sharing logs
- Consider sanitizing logs before sharing

## Performance Impact

- Console logging: Minimal impact
- File logging: Low impact (~1-2% overhead)
- DEBUG level: Moderate impact (~5-10% overhead)
- JSON format: Slightly higher than text format

## Troubleshooting Logging Issues

### Logs Not Being Created

1. Check log directory exists and is writable:
   ```bash
   mkdir -p logs
   chmod 755 logs
   ```

2. Check config.yaml syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

3. Verify file path is absolute or relative to working directory

### Too Much Log Output

1. Increase log level to WARNING or ERROR:
   ```yaml
   level: "WARNING"
   ```

2. Disable command/tool logging:
   ```yaml
   log_commands: false
   log_tools: false
   ```

3. Disable console logging:
   ```yaml
   enable_console: false
   ```

### Logs Missing Information

1. Lower log level to DEBUG:
   ```yaml
   level: "DEBUG"
   ```

2. Ensure command/tool logging is enabled:
   ```yaml
   log_commands: true
   log_tools: true
   ```

## Integration with External Tools

### With ELK Stack

```yaml
json_format: true
file: "/var/log/kali-driver-mcp/server.log"
```

Configure Filebeat to ship to Elasticsearch.

### With Splunk

```yaml
json_format: true
file: "/opt/splunk/var/log/kali-driver-mcp.log"
```

### With CloudWatch

Use AWS CloudWatch agent to ship logs.

### With Syslog

```python
# Add syslog handler in logging_config.py
from logging.handlers import SysLogHandler

syslog_handler = SysLogHandler(address='/dev/log')
logger.addHandler(syslog_handler)
```

---

For questions or issues with logging, check the main documentation or open an issue.
