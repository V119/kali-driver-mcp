"""Network interface information tool."""

from typing import Dict, Any, Optional
from ..config import Config
from ..ssh_manager import SSHManager


async def get_network_info(
    config: Config,
    ssh: SSHManager,
    interface: str = "all",
    detail_level: str = "basic",
    info_type: str = "status"
) -> Dict[str, Any]:
    """
    Query network interface information.

    Args:
        config: Configuration object
        ssh: SSH manager
        interface: Interface name or "all"
        detail_level: "basic", "detailed", or "statistics"
        info_type: "status", "driver", "settings", or "stats"

    Returns:
        Dictionary with network interface information
    """
    result = {
        "interface": interface,
        "detail_level": detail_level,
        "info_type": info_type
    }

    if interface == "all":
        # List all interfaces
        cmd = "ip link"
        exec_result = await ssh.execute(cmd)

        if exec_result.success:
            result["success"] = True
            result["output"] = exec_result.stdout

            # Also list interface names
            list_cmd = "ls /sys/class/net/"
            list_result = await ssh.execute(list_cmd)
            if list_result.success:
                result["interfaces"] = list_result.stdout.split()
        else:
            result["success"] = False
            result["error"] = exec_result.stderr

    else:
        # Specific interface
        interface_data = {}

        if info_type == "status" or detail_level in ["detailed", "statistics"]:
            # Get link status
            link_cmd = f"ip link show {interface}"
            link_result = await ssh.execute(link_cmd)
            if link_result.success:
                interface_data["link_info"] = link_result.stdout

            # Get addresses
            addr_cmd = f"ip addr show {interface}"
            addr_result = await ssh.execute(addr_cmd)
            if addr_result.success:
                interface_data["addr_info"] = addr_result.stdout

            # Get operational state
            state_cmd = f"cat /sys/class/net/{interface}/operstate 2>/dev/null"
            state_result = await ssh.execute(state_cmd)
            if state_result.success:
                interface_data["state"] = state_result.stdout

            # Get MAC address
            mac_cmd = f"cat /sys/class/net/{interface}/address 2>/dev/null"
            mac_result = await ssh.execute(mac_cmd)
            if mac_result.success:
                interface_data["mac_address"] = mac_result.stdout

        if info_type == "driver" or detail_level == "detailed":
            # Get driver information using ethtool
            driver_cmd = f"ethtool -i {interface} 2>/dev/null"
            driver_result = await ssh.execute(driver_cmd)
            if driver_result.success:
                interface_data["driver_info"] = driver_result.stdout

        if info_type == "stats" or detail_level == "statistics":
            # Get statistics
            stats_cmd = f"ip -s link show {interface}"
            stats_result = await ssh.execute(stats_cmd)
            if stats_result.success:
                interface_data["statistics"] = stats_result.stdout

            # Get detailed stats from sysfs
            rx_packets_cmd = f"cat /sys/class/net/{interface}/statistics/rx_packets 2>/dev/null"
            tx_packets_cmd = f"cat /sys/class/net/{interface}/statistics/tx_packets 2>/dev/null"
            rx_bytes_cmd = f"cat /sys/class/net/{interface}/statistics/rx_bytes 2>/dev/null"
            tx_bytes_cmd = f"cat /sys/class/net/{interface}/statistics/tx_bytes 2>/dev/null"

            rx_packets = await ssh.execute(rx_packets_cmd)
            tx_packets = await ssh.execute(tx_packets_cmd)
            rx_bytes = await ssh.execute(rx_bytes_cmd)
            tx_bytes = await ssh.execute(tx_bytes_cmd)

            if all([rx_packets.success, tx_packets.success, rx_bytes.success, tx_bytes.success]):
                interface_data["detailed_stats"] = {
                    "rx_packets": rx_packets.stdout,
                    "tx_packets": tx_packets.stdout,
                    "rx_bytes": rx_bytes.stdout,
                    "tx_bytes": tx_bytes.stdout
                }

        # Check if it's a wireless interface
        wireless_check = await ssh.execute(f"iw dev {interface} info 2>/dev/null")
        if wireless_check.success:
            interface_data["wireless"] = True
            interface_data["wireless_info"] = wireless_check.stdout
        else:
            interface_data["wireless"] = False

        result["success"] = True
        result["interface_data"] = interface_data

    return result
