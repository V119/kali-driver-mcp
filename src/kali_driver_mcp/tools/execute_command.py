"""Execute arbitrary shell commands on Kali VM.

This tool allows executing any shell command on the Kali VM.
Use with caution as it has full system access (via sudo).
"""

import logging
from typing import Dict, Any
from ..ssh_manager import SSHManager

logger = logging.getLogger(__name__)


async def execute_command(
    ssh_manager: SSHManager,
    command: str,
    use_sudo: bool = False,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Execute a shell command on the Kali VM.

    Args:
        ssh_manager: SSH connection manager
        command: Command to execute
        use_sudo: Whether to run with sudo
        timeout: Command timeout in seconds

    Returns:
        Result containing command output and status
    """
    try:
        # Prepare command
        if use_sudo:
            # Already handled by ssh_manager's execute_command
            pass

        # Execute command
        exit_code, stdout, stderr = await ssh_manager.execute_command(
            command,
            timeout=timeout
        )

        success = exit_code == 0

        result = {
            "success": success,
            "exit_code": exit_code,
            "stdout": stdout.strip() if stdout else "",
            "stderr": stderr.strip() if stderr else "",
            "command": command
        }

        if not success:
            result["error"] = f"Command exited with code {exit_code}"
            if stderr:
                result["error"] += f": {stderr.strip()}"

        return result

    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": f"Command timed out after {timeout} seconds",
            "command": command
        }
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": command
        }
