"""Log viewing tool."""

from typing import Dict, Any, Optional
from ..config import Config
from ..ssh_manager import SSHManager


async def view_logs(
    config: Config,
    ssh: SSHManager,
    source: Optional[str] = None,
    lines: Optional[int] = None,
    follow: bool = False,
    filter_pattern: Optional[str] = None,
    level: Optional[str] = None,
    since: Optional[str] = None
) -> Dict[str, Any]:
    """
    Access kernel and system logs.

    Args:
        config: Configuration object
        ssh: SSH manager
        source: "dmesg", "syslog", "kern", or "journal"
        lines: Number of lines to retrieve
        follow: Continuous monitoring (not practical via MCP)
        filter_pattern: Regex pattern to filter logs
        level: Log level filter ("error", "warn", "info", "debug")
        since: Time filter (e.g., "5 min ago")

    Returns:
        Dictionary with log entries
    """
    if source is None:
        source = config.logging.default_source

    if lines is None:
        lines = config.logging.max_lines

    result = {
        "source": source,
        "lines": lines,
        "entries": []
    }

    cmd = ""

    if source == "dmesg":
        cmd = "dmesg"
        if level:
            cmd += f" --level={level}"
        if since:
            cmd += f' --since "{since}"'
        cmd += " -T"  # Human-readable timestamps

    elif source == "syslog":
        cmd = f"tail -n {lines} /var/log/syslog"

    elif source == "kern":
        cmd = f"tail -n {lines} /var/log/kern.log"

    elif source == "journal":
        cmd = "journalctl -k"  # kernel messages
        if lines:
            cmd += f" -n {lines}"
        if since:
            cmd += f' --since "{since}"'

    else:
        result["error"] = f"Unknown log source: {source}"
        return result

    # Apply filter if provided
    if filter_pattern:
        cmd += f" | grep '{filter_pattern}'"

    # Limit lines if not already limited
    if source == "dmesg" and lines:
        cmd += f" | tail -n {lines}"

    exec_result = await ssh.execute(cmd, timeout=60)

    if exec_result.success:
        result["success"] = True
        log_lines = exec_result.stdout.split("\n") if exec_result.stdout else []
        result["entries"] = log_lines
        result["total_entries"] = len(log_lines)
    else:
        result["success"] = False
        result["error"] = exec_result.stderr

    return result
