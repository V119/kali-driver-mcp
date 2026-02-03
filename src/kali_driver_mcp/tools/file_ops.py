"""File operations tool."""

from typing import Dict, Any, List, Optional
from ..config import Config
from ..ssh_manager import SSHManager


async def file_operations(
    config: Config,
    ssh: SSHManager,
    operation: str = "list",
    path: Optional[str] = None,
    recursive: bool = False,
    filter_pattern: Optional[str] = None,
    search_pattern: Optional[str] = None
) -> Dict[str, Any]:
    """
    List and browse files in the VM.

    Args:
        config: Configuration object
        ssh: SSH manager
        operation: "list", "read", "stat", or "search"
        path: Directory or file path (default: config.shared_folder.vm_path)
        recursive: Boolean for recursive listing
        filter_pattern: File pattern filter (e.g., "*.c")
        search_pattern: Pattern for content search

    Returns:
        Dictionary with operation results
    """
    # Default to shared folder path
    if path is None:
        path = config.shared_folder.vm_path

    result = {"operation": operation, "path": path}

    if operation == "list":
        if recursive:
            cmd = f"ls -R {path}"
        else:
            cmd = f"ls -lah {path}"

        if filter_pattern:
            cmd = f"find {path} -name '{filter_pattern}'"

        exec_result = await ssh.execute(cmd)
        if exec_result.success:
            result["output"] = exec_result.stdout
            # Parse file entries
            result["entries"] = exec_result.stdout.split("\n")
        else:
            result["error"] = exec_result.stderr

    elif operation == "read":
        cmd = f"cat {path}"
        exec_result = await ssh.execute(cmd)
        if exec_result.success:
            result["content"] = exec_result.stdout
        else:
            result["error"] = exec_result.stderr

    elif operation == "stat":
        cmd = f"stat {path}"
        exec_result = await ssh.execute(cmd)
        if exec_result.success:
            result["stat_info"] = exec_result.stdout
        else:
            result["error"] = exec_result.stderr

    elif operation == "search":
        if not search_pattern:
            result["error"] = "search_pattern is required for search operation"
        else:
            cmd = f"grep -r '{search_pattern}' {path}"
            exec_result = await ssh.execute(cmd)
            # grep returns 1 if no matches, which is not an error
            if exec_result.exit_code in [0, 1]:
                result["matches"] = exec_result.stdout.split("\n") if exec_result.stdout else []
            else:
                result["error"] = exec_result.stderr

    else:
        result["error"] = f"Unknown operation: {operation}"

    return result
