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
    force: bool = False,
    use_modprobe: bool = True,
    module_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load, unload, or get info about kernel modules.

    Args:
        config: Configuration object
        ssh: SSH manager
        operation: "load", "unload", "reload", "info", "list", or "install"
        module_name: Module name (without .ko extension)
        parameters: Module parameters (key=value pairs)
        force: Force unload
        use_modprobe: Use modprobe instead of insmod (default: True)
        module_path: Optional path to .ko file (for insmod)

    Returns:
        Dictionary with operation results
    """
    vm_path = config.shared_folder.vm_path
    result = {
        "operation": operation,
        "module_name": module_name,
        "success": False
    }

    if operation == "install":
        # Run make install in the driver directory
        install_dir = module_path or f"{vm_path}/drivers/aic8800"
        install_cmd = f"cd {install_dir} && make install"

        exec_result = await ssh.execute(install_cmd, timeout=120, needs_root=True)
        result["success"] = exec_result.success

        if exec_result.success:
            result["message"] = "Modules installed successfully"
            result["output"] = exec_result.stdout

            # Run depmod to update module dependencies
            depmod_result = await ssh.execute("depmod -a", needs_root=True)
            if depmod_result.success:
                result["depmod_run"] = True
        else:
            result["error"] = exec_result.stderr or exec_result.stdout

    elif operation == "load":
        if use_modprobe:
            # Use modprobe (for installed modules)
            cmd = f"modprobe {module_name}"

            # Add parameters if provided
            if parameters:
                params_str = " ".join([f"{k}={v}" for k, v in parameters.items()])
                cmd += f" {params_str}"

            exec_result = await ssh.execute(cmd, needs_root=True)
            result["success"] = exec_result.success

            if exec_result.success:
                result["message"] = f"Module {module_name} loaded successfully via modprobe"
                result["method"] = "modprobe"
            else:
                result["error"] = exec_result.stderr
        else:
            # Use insmod (for local .ko files)
            if not module_path:
                module_path = f"{vm_path}/{module_name}.ko"

            # Check if module file exists
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

            exec_result = await ssh.execute(cmd, needs_root=True)
            result["success"] = exec_result.success

            if exec_result.success:
                result["message"] = f"Module {module_name} loaded successfully via insmod"
                result["method"] = "insmod"
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
