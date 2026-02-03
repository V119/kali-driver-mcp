"""Network monitoring tool (airmon-ng)."""

from typing import Dict, Any, Optional
from ..config import Config
from ..ssh_manager import SSHManager


async def manage_monitor_mode(
    config: Config,
    ssh: SSHManager,
    operation: str,
    channel: Optional[int] = None
) -> Dict[str, Any]:
    """
    Start or stop wireless monitor mode using airmon-ng.

    Args:
        config: Configuration object
        ssh: SSH manager
        operation: "start" or "stop"
        channel: Optional channel number (overrides config)

    Returns:
        Dictionary with operation results
    """
    wireless_interface = config.network.wireless_interface
    monitor_interface = config.network.monitor_interface
    default_channel = channel or config.network.default_channel
    kill_processes = config.network.kill_processes

    result = {
        "operation": operation,
        "wireless_interface": wireless_interface,
        "monitor_interface": monitor_interface,
        "success": False
    }

    if operation == "start":
        # Kill interfering processes if configured
        if kill_processes:
            kill_cmd = "airmon-ng check kill"
            kill_result = await ssh.execute(kill_cmd, timeout=30, needs_root=True)
            if kill_result.success:
                result["killed_processes"] = kill_result.stdout

        # Start monitor mode
        if channel:
            cmd = f"airmon-ng start {wireless_interface} {channel}"
        else:
            cmd = f"airmon-ng start {wireless_interface}"

        exec_result = await ssh.execute(cmd, timeout=30, needs_root=True)  # Needs root

        if exec_result.exit_code == 0:
            result["success"] = True
            result["output"] = exec_result.stdout

            # Verify monitor interface was created
            verify_cmd = f"iw dev {monitor_interface} info 2>/dev/null"
            verify_result = await ssh.execute(verify_cmd)

            if verify_result.success:
                result["monitor_interface_active"] = True
                result["interface_info"] = verify_result.stdout

                # Extract mode from output
                for line in verify_result.stdout.split("\n"):
                    if "type" in line.lower():
                        result["mode"] = line.split()[-1]
                    if "channel" in line.lower():
                        result["channel"] = line.split()[-1]
            else:
                result["monitor_interface_active"] = False
        else:
            result["error"] = exec_result.stderr or exec_result.stdout

    elif operation == "stop":
        # Stop monitor mode
        cmd = f"airmon-ng stop {monitor_interface}"
        exec_result = await ssh.execute(cmd, timeout=30, needs_root=True)  # Needs root

        if exec_result.exit_code == 0:
            result["success"] = True
            result["output"] = exec_result.stdout

            # Verify original interface is back
            verify_cmd = f"ip link show {wireless_interface} 2>/dev/null"
            verify_result = await ssh.execute(verify_cmd)

            if verify_result.success:
                result["wireless_interface_restored"] = True
            else:
                result["wireless_interface_restored"] = False
        else:
            result["error"] = exec_result.stderr or exec_result.stdout

    elif operation == "status":
        # Check current status
        status_cmd = "airmon-ng"
        status_result = await ssh.execute(status_cmd)

        if status_result.success:
            result["success"] = True
            result["status"] = status_result.stdout

            # Check if monitor interface exists
            monitor_check = await ssh.execute(f"ip link show {monitor_interface} 2>/dev/null")
            result["monitor_mode_active"] = monitor_check.success
        else:
            result["error"] = status_result.stderr

    else:
        result["error"] = f"Unknown operation: {operation}"

    return result
