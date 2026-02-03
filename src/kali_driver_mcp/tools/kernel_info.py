"""Kernel information tool."""

from typing import Dict, Any
from ..config import Config
from ..ssh_manager import SSHManager


async def get_kernel_info(
    config: Config,
    ssh: SSHManager,
    detail_level: str = "basic"
) -> Dict[str, Any]:
    """
    Get kernel version and configuration information.

    Args:
        config: Configuration object
        ssh: SSH manager
        detail_level: "basic" or "full"

    Returns:
        Dictionary with kernel information
    """
    result = {}

    # Always get basic info
    version_result = await ssh.execute("uname -r")
    if version_result.success:
        result["version"] = version_result.stdout

    arch_result = await ssh.execute("uname -m")
    if arch_result.success:
        result["architecture"] = arch_result.stdout

    if detail_level == "full":
        # Full system info
        full_result = await ssh.execute("uname -a")
        if full_result.success:
            result["full_info"] = full_result.stdout

        # Detailed version
        proc_version = await ssh.execute("cat /proc/version")
        if proc_version.success:
            result["proc_version"] = proc_version.stdout

        # Kernel build date
        build_date = await ssh.execute("uname -v")
        if build_date.success:
            result["build_date"] = build_date.stdout

        # Loaded modules count
        modules_count = await ssh.execute("lsmod | wc -l")
        if modules_count.success:
            try:
                # Subtract 1 for header line
                count = int(modules_count.stdout.strip()) - 1
                result["loaded_modules_count"] = count
            except ValueError:
                result["loaded_modules_count"] = 0

    return result
