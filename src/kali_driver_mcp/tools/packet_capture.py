"""Packet capture tool (airodump-ng)."""

import asyncio
from typing import Dict, Any, Optional
from ..config import Config
from ..ssh_manager import SSHManager


async def capture_packets(
    config: Config,
    ssh: SSHManager,
    channel: Optional[int] = None,
    bssid: Optional[str] = None,
    duration: Optional[int] = None,
    output_prefix: str = "capture"
) -> Dict[str, Any]:
    """
    Capture wireless packets using airodump-ng.

    Args:
        config: Configuration object
        ssh: SSH manager
        channel: Optional channel override
        bssid: Optional specific AP MAC address
        duration: Optional duration override (seconds)
        output_prefix: Filename prefix for capture files

    Returns:
        Dictionary with capture results
    """
    monitor_interface = config.network.monitor_interface
    capture_channel = channel or config.network.default_channel
    capture_duration = duration or config.capture.default_duration
    output_dir = config.capture.output_dir
    output_format = config.capture.output_format
    update_interval = config.capture.update_interval
    band = config.capture.band

    result = {
        "monitor_interface": monitor_interface,
        "channel": capture_channel,
        "duration": capture_duration,
        "output_prefix": output_prefix,
        "success": False
    }

    # Verify monitor interface exists
    check_cmd = f"ip link show {monitor_interface} 2>/dev/null"
    check_result = await ssh.execute(check_cmd)
    if not check_result.success:
        result["error"] = f"Monitor interface {monitor_interface} not found. Run network_monitor start first."
        return result

    # Ensure output directory exists
    mkdir_cmd = f"mkdir -p {output_dir}"
    await ssh.execute(mkdir_cmd)

    # Build airodump-ng command
    output_path = f"{output_dir}/{output_prefix}"
    cmd = f"timeout {capture_duration} airodump-ng"

    # Add channel
    cmd += f" -c {capture_channel}"

    # Add output file
    cmd += f" -w {output_path}"

    # Add output format
    cmd += f" --output-format {output_format}"

    # Add update interval
    cmd += f" --update {update_interval}"

    # Add band selection
    cmd += f" --band {band}"

    # Add BSSID filter if provided
    if bssid:
        cmd += f" --bssid {bssid}"

    # Add interface
    cmd += f" {monitor_interface}"

    # Background mode to avoid interactive output issues
    cmd += " --background 1"

    # Execute capture with extended timeout
    exec_result = await ssh.execute(cmd, timeout=capture_duration + 10, needs_root=True)  # Needs root

    # Note: timeout command returns 124 when it times out (which is expected)
    if exec_result.exit_code in [0, 124]:
        result["success"] = True
        result["output"] = exec_result.stdout

        # List generated files
        list_cmd = f"ls -lh {output_dir}/{output_prefix}* 2>/dev/null"
        list_result = await ssh.execute(list_cmd)

        if list_result.success:
            result["capture_files"] = []
            for line in list_result.stdout.split("\n"):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 9:
                        filename = parts[-1]
                        filesize = parts[4]
                        result["capture_files"].append({
                            "filename": filename,
                            "size": filesize
                        })

        # Parse CSV file if it exists
        csv_files = [f for f in result.get("capture_files", []) if f["filename"].endswith(".csv")]
        if csv_files:
            csv_path = csv_files[0]["filename"]
            csv_cmd = f"cat {csv_path}"
            csv_result = await ssh.execute(csv_cmd)

            if csv_result.success:
                result["csv_data"] = csv_result.stdout
                # Parse networks from CSV
                result["networks"] = _parse_airodump_csv(csv_result.stdout)

        # Count packets in cap file if exists
        cap_files = [f for f in result.get("capture_files", []) if f["filename"].endswith(".cap")]
        if cap_files:
            cap_path = cap_files[0]["filename"]
            count_cmd = f"tcpdump -r {cap_path} 2>/dev/null | wc -l"
            count_result = await ssh.execute(count_cmd)

            if count_result.success:
                try:
                    result["packets_captured"] = int(count_result.stdout.strip())
                except ValueError:
                    result["packets_captured"] = 0

    else:
        result["error"] = exec_result.stderr or exec_result.stdout

    return result


def _parse_airodump_csv(csv_content: str) -> list:
    """Parse airodump-ng CSV output to extract network information."""
    networks = []

    lines = csv_content.split("\n")
    in_ap_section = False

    for line in lines:
        line = line.strip()

        if line.startswith("BSSID"):
            in_ap_section = True
            continue

        if in_ap_section and line and not line.startswith("Station"):
            parts = [p.strip() for p in line.split(",")]

            if len(parts) >= 14:
                try:
                    network = {
                        "bssid": parts[0],
                        "first_seen": parts[1],
                        "last_seen": parts[2],
                        "channel": parts[3],
                        "speed": parts[4],
                        "privacy": parts[5],
                        "cipher": parts[6],
                        "authentication": parts[7],
                        "power": parts[8],
                        "beacons": parts[9],
                        "iv": parts[10],
                        "lan_ip": parts[11],
                        "id_length": parts[12],
                        "essid": parts[13]
                    }
                    networks.append(network)
                except (IndexError, ValueError):
                    continue

        if line.startswith("Station"):
            break

    return networks
