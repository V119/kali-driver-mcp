"""Code synchronization tool."""

from typing import Dict, Any
from ..config import Config
from ..ssh_manager import SSHManager


async def verify_shared_folder(
    config: Config,
    ssh: SSHManager
) -> Dict[str, Any]:
    """
    Verify shared folder is mounted and accessible.

    Args:
        config: Configuration object
        ssh: SSH manager

    Returns:
        Dictionary with verification status
    """
    vm_path = config.shared_folder.vm_path
    result = {
        "vm_path": vm_path,
        "mounted": False,
        "writable": False,
        "files_count": 0,
        "mount_type": None
    }

    # Check if mount point exists
    exists_check = await ssh.execute(f"test -d {vm_path} && echo EXISTS || echo NOT_FOUND", needs_root=True)
    if exists_check.stdout == "NOT_FOUND":
        result["error"] = f"Directory not found: {vm_path}"
        return result

    # Check if mounted (look for shared folder in mount output)
    mount_check = await ssh.execute("mount | grep kali-share || mount | grep vboxsf || mount | grep vmhgfs")
    if mount_check.success and mount_check.stdout:
        result["mounted"] = True
        result["mount_info"] = mount_check.stdout

        # Extract mount type from mount output
        for line in mount_check.stdout.split("\n"):
            if "kali-share" in line or "vboxsf" in line or "vmhgfs" in line:
                parts = line.split()
                if len(parts) >= 5:
                    result["mount_type"] = parts[4].strip("()")
                break

    # Check if writable (use root to test)
    writable_check = await ssh.execute(f"test -w {vm_path} && echo WRITABLE || echo READ_ONLY", needs_root=True)
    if writable_check.stdout == "WRITABLE":
        result["writable"] = True

    # Count files (use root to access)
    files_count = await ssh.execute(f"ls -1 {vm_path} 2>/dev/null | wc -l", needs_root=True)
    if files_count.success:
        try:
            result["files_count"] = int(files_count.stdout.strip())
        except ValueError:
            pass

    # Check for Makefile (use root to access)
    makefile_check = await ssh.execute(f"test -f {vm_path}/Makefile && echo YES || echo NO", needs_root=True)
    result["has_makefile"] = (makefile_check.stdout == "YES")

    # Overall status
    result["ready"] = result["writable"] and result["files_count"] > 0

    return result
