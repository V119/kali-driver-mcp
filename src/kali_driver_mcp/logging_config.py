"""Logging configuration and utilities."""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import traceback


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


class CommandLogger:
    """Logger for SSH command execution with detailed tracking."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.command_counter = 0

    def log_command_start(
        self,
        command: str,
        timeout: Optional[int] = None,
        context: Optional[dict] = None
    ) -> int:
        """
        Log command start.

        Args:
            command: Command to execute
            timeout: Command timeout
            context: Additional context information

        Returns:
            Command ID for tracking
        """
        self.command_counter += 1
        cmd_id = self.command_counter

        log_data = {
            "cmd_id": cmd_id,
            "command": command,
            "timeout": timeout,
            "started_at": datetime.utcnow().isoformat(),
        }

        if context:
            log_data["context"] = context

        # Log command start with full command
        command_preview = command[:200] if len(command) > 200 else command
        truncated = "... (truncated, see full command below)" if len(command) > 200 else ""

        self.logger.info(
            f"[CMD-{cmd_id}] Starting command: {command_preview}{truncated}",
            extra={"extra_data": log_data}
        )

        # If command is long, log full command separately
        if len(command) > 200:
            self.logger.info(
                f"[CMD-{cmd_id}] Full command:\n{command}"
            )

        return cmd_id

    def log_command_end(
        self,
        cmd_id: int,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration: float
    ):
        """
        Log command completion.

        Args:
            cmd_id: Command ID
            exit_code: Exit code
            stdout: Standard output
            stderr: Standard error
            duration: Execution duration in seconds
        """
        log_data = {
            "cmd_id": cmd_id,
            "exit_code": exit_code,
            "stdout_length": len(stdout),
            "stderr_length": len(stderr),
            "duration_seconds": round(duration, 3),
            "completed_at": datetime.utcnow().isoformat(),
        }

        # Always include full output in log data (for JSON format)
        log_data["stdout"] = stdout
        log_data["stderr"] = stderr

        level = logging.INFO if exit_code == 0 else logging.WARNING

        # Log completion message
        self.logger.log(
            level,
            f"[CMD-{cmd_id}] Completed with exit code {exit_code} in {duration:.3f}s",
            extra={"extra_data": log_data}
        )

        # Log stdout if present (as separate INFO message for readability)
        if stdout:
            stdout_preview = stdout[:500] if len(stdout) > 500 else stdout
            truncated = "... (truncated)" if len(stdout) > 500 else ""
            self.logger.info(
                f"[CMD-{cmd_id}] STDOUT:\n{stdout_preview}{truncated}"
            )

        # Log stderr if present (as WARNING for visibility)
        if stderr:
            stderr_preview = stderr[:500] if len(stderr) > 500 else stderr
            truncated = "... (truncated)" if len(stderr) > 500 else ""
            self.logger.warning(
                f"[CMD-{cmd_id}] STDERR:\n{stderr_preview}{truncated}"
            )

    def log_command_error(self, cmd_id: int, error: Exception):
        """
        Log command error.

        Args:
            cmd_id: Command ID
            error: Exception that occurred
        """
        self.logger.error(
            f"[CMD-{cmd_id}] Command failed with error: {error}",
            extra={"extra_data": {
                "cmd_id": cmd_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
            }},
            exc_info=True
        )


class ToolLogger:
    """Logger for MCP tool execution."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.tool_counter = 0

    def log_tool_start(self, tool_name: str, arguments: dict) -> int:
        """
        Log tool invocation start.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tool invocation ID
        """
        self.tool_counter += 1
        tool_id = self.tool_counter

        log_data = {
            "tool_id": tool_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "started_at": datetime.utcnow().isoformat(),
        }

        self.logger.info(
            f"[TOOL-{tool_id}] Invoking tool: {tool_name}",
            extra={"extra_data": log_data}
        )

        return tool_id

    def log_tool_end(
        self,
        tool_id: int,
        tool_name: str,
        result: Any,
        duration: float,
        success: bool = True
    ):
        """
        Log tool completion.

        Args:
            tool_id: Tool invocation ID
            tool_name: Name of the tool
            result: Tool result
            duration: Execution duration
            success: Whether tool succeeded
        """
        log_data = {
            "tool_id": tool_id,
            "tool_name": tool_name,
            "duration_seconds": round(duration, 3),
            "success": success,
            "completed_at": datetime.utcnow().isoformat(),
        }

        # Log result summary
        if isinstance(result, dict):
            log_data["result_keys"] = list(result.keys())
            if "error" in result:
                log_data["error"] = result["error"]

        level = logging.INFO if success else logging.ERROR

        self.logger.log(
            level,
            f"[TOOL-{tool_id}] Tool {tool_name} completed in {duration:.3f}s",
            extra={"extra_data": log_data}
        )

    def log_tool_error(self, tool_id: int, tool_name: str, error: Exception):
        """
        Log tool error.

        Args:
            tool_id: Tool invocation ID
            tool_name: Name of the tool
            error: Exception that occurred
        """
        self.logger.error(
            f"[TOOL-{tool_id}] Tool {tool_name} failed: {error}",
            extra={"extra_data": {
                "tool_id": tool_id,
                "tool_name": tool_name,
                "error_type": type(error).__name__,
                "error_message": str(error),
            }},
            exc_info=True
        )


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
    enable_console: bool = True
) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        json_format: Use JSON format for logs
        enable_console: Enable console output

    Returns:
        Configured root logger
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        if json_format:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)

        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用追加模式 'a' 而不是覆盖模式 'w'
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file

        if json_format:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)

        root_logger.addHandler(file_handler)

    return root_logger


def get_command_logger(name: str = "ssh_commands") -> CommandLogger:
    """Get a command logger instance."""
    logger = logging.getLogger(name)
    return CommandLogger(logger)


def get_tool_logger(name: str = "mcp_tools") -> ToolLogger:
    """Get a tool logger instance."""
    logger = logging.getLogger(name)
    return ToolLogger(logger)
