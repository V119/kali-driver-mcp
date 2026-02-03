"""Driver compilation tool."""

import time
from typing import Dict, Any, Optional, List
from ..config import Config
from ..ssh_manager import SSHManager


async def compile_driver(
    config: Config,
    ssh: SSHManager,
    target: Optional[str] = None,
    clean: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Compile kernel modules using make.

    Args:
        config: Configuration object
        ssh: SSH manager
        target: Optional specific make target (default: all)
        clean: Force clean build
        verbose: Verbose output

    Returns:
        Dictionary with compilation results
    """
    vm_path = config.shared_folder.vm_path
    make_jobs = config.build.make_jobs
    should_clean = clean or config.build.clean_before_build

    result = {
        "vm_path": vm_path,
        "target": target or "all",
        "cleaned": False,
        "success": False,
        "artifacts": []
    }

    # Check if Makefile exists
    makefile_check = await ssh.execute(f"test -f {vm_path}/Makefile && echo YES || echo NO")
    if makefile_check.stdout != "YES":
        result["error"] = f"Makefile not found in {vm_path}"
        return result

    # Clean if requested
    if should_clean:
        clean_cmd = f"cd {vm_path} && make clean"
        clean_result = await ssh.execute(clean_cmd, timeout=60)
        result["cleaned"] = clean_result.success
        if not clean_result.success:
            result["clean_error"] = clean_result.stderr

    # Build command
    make_cmd = f"cd {vm_path} && make -j{make_jobs}"
    if verbose:
        make_cmd += " V=1"
    if target:
        make_cmd += f" {target}"

    # Execute build with longer timeout (5 minutes)
    start_time = time.time()
    build_result = await ssh.execute(make_cmd, timeout=300)
    duration = time.time() - start_time

    result["duration"] = round(duration, 2)
    result["exit_code"] = build_result.exit_code
    result["success"] = build_result.success

    if build_result.success:
        result["output"] = build_result.stdout

        # Find compiled .ko files
        find_cmd = f"find {vm_path} -name '*.ko' -type f"
        find_result = await ssh.execute(find_cmd)
        if find_result.success and find_result.stdout:
            result["artifacts"] = find_result.stdout.split("\n")
    else:
        result["error"] = build_result.stderr or build_result.stdout

    return result
