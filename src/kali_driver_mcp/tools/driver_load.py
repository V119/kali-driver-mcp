"""Driver loading/unloading tool."""

from typing import Dict, Any, Optional
from ..config import Config
from ..ssh_manager import SSHManager


async def manage_driver(
    config: Config,
    ssh: SSHManager,
    operation: str,
    module_name: str,
    parameters: Optional[Dict[str, str]] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Load, unload, or get info about kernel modules.

    Args:
        config: Configuration object
        ssh: SSH manager
        operation: "load", "unload", "reload", "info", or "list"
        module_name: Module name (without .ko extension)
        parameters: Module parameters (key=value pairs)
        force: Force unload

    Returns:
        Dictionary with operation results
    """
    vm_path = config.shared_folder.vm_path
    result = {
        "operation": operation,
        "module_name": module_name,
        "success": False
    }

    if operation == "load":
        # Build insmod command
        module_path = f"{vm_path}/{module_name}.ko"

        # Check if module file exists (use root to access shared folder)
        check_cmd = f"test -f {module_path} && echo YES || echo NO"
        check_result = await ssh.execute(check_cmd, needs_root=True)
        if check_result.stdout != "YES":
            result["error"] = f"Module file not found: {module_path}"
            return result

        cmd = f"insmod {module_path}"

        # Add parameters if provided
        if parameters:
            params_str = " ".join([f"{k}={v}" for k, v in parameters.items()])
            cmd += f" {params_str}"

        exec_result = await ssh.execute(cmd, needs_root=True)  # Needs root
        result["success"] = exec_result.success

        if exec_result.success:
            result["message"] = f"Module {module_name} loaded successfully"
        else:
            result["error"] = exec_result.stderr

    elif operation == "unload":
        cmd = f"rmmod {module_name}"
        if force:
            cmd += " -f"

        exec_result = await ssh.execute(cmd, needs_root=True)  # Needs root
        result["success"] = exec_result.success

        if exec_result.success:
            result["message"] = f"Module {module_name} unloaded successfully"
        else:
            result["error"] = exec_result.stderr

    elif operation == "reload":
        # Unload first
        unload_result = await ssh.execute(f"rmmod {module_name}", needs_root=True)

        # Then load
        module_path = f"{vm_path}/{module_name}.ko"
        load_cmd = f"insmod {module_path}"
        if parameters:
            params_str = " ".join([f"{k}={v}" for k, v in parameters.items()])
            load_cmd += f" {params_str}"

        load_result = await ssh.execute(load_cmd, needs_root=True)  # Needs root
        result["success"] = load_result.success

        if load_result.success:
            result["message"] = f"Module {module_name} reloaded successfully"
        else:
            result["error"] = load_result.stderr

    elif operation == "info":
        # First try to get info from file
        module_path = f"{vm_path}/{module_name}.ko"
        file_info_cmd = f"modinfo {module_path} 2>/dev/null || modinfo {module_name}"

        info_result = await ssh.execute(file_info_cmd)

        if info_result.success:
            result["success"] = True
            result["info"] = info_result.stdout

            # Parse key information
            info_dict = {}
            for line in info_result.stdout.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    info_dict[key.strip()] = value.strip()
            result["parsed_info"] = info_dict
        else:
            result["error"] = "Module information not available"

        # Check if module is loaded
        lsmod_result = await ssh.execute(f"lsmod | grep '^{module_name} '")
        result["loaded"] = lsmod_result.success

    elif operation == "list":
        # List all loaded modules
        lsmod_result = await ssh.execute("lsmod")

        if lsmod_result.success:
            result["success"] = True
            result["modules"] = lsmod_result.stdout.split("\n")
        else:
            result["error"] = lsmod_result.stderr

    else:
        result["error"] = f"Unknown operation: {operation}"

    return result
