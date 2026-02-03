"""Pytest fixtures for kali-driver-mcp tests."""

import pytest
import pytest_asyncio
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock
from kali_driver_mcp.config import Config
from kali_driver_mcp.ssh_manager import SSHManager, CommandResult
from kali_driver_mcp.logging_config import setup_logging


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Configure logging for all tests - runs automatically."""
    # 设置应用程序日志（会写入 logs/kali-driver-mcp.log）
    setup_logging(
        log_level="DEBUG",
        log_file="logs/kali-driver-mcp.log",
        json_format=False,
        enable_console=False  # pytest 会处理控制台输出
    )
    yield
    # 测试结束后清理
    logging.shutdown()


@pytest.fixture
def test_config_data() -> Dict[str, Any]:
    """Return minimal test configuration data."""
    return {
        "vm": {
            "host": "192.168.2.104",
            "port": 22,
            "username": "kali",
            "auth_method": "password",
            "key_file": None,
            "password": "kali",
            "use_sudo": True,
            "sudo_method": "su",
            "sudo_password": "kali"
        },
        "shared_folder": {
            "host_path": "/Users/haoyang/src/AIC8800-Linux-Driver",
            "vm_path": "/home/kali/Desktop/share/AIC8800-Linux-Driver",
            "verify_mount": True
        },
        "build": {
            "make_jobs": 4,
            "clean_before_build": False
        },
        "network": {
            "wireless_interface": "wlan0",
            "monitor_interface": "wlan0mon",
            "default_channel": 6,
            "kill_processes": True
        },
        "capture": {
            "output_dir": "/tmp/captures",
            "default_duration": 60,
            "output_format": "pcap,csv",
            "update_interval": 1,
            "band": "bg"
        },
        "logging": {
            "max_lines": 1000,
            "default_source": "dmesg",
            "level": "INFO",
            "file": "logs/kali-driver-mcp.log",
            "json_format": False,
            "enable_console": True,
            "log_commands": True,
            "log_tools": True
        }
    }


@pytest.fixture
def test_config(test_config_data) -> Config:
    """Return a Config object with test data."""
    return Config.from_dict(test_config_data)


@pytest.fixture
def test_config_with_sudo(test_config_data) -> Config:
    """Return a Config object with sudo enabled."""
    config_data = test_config_data.copy()
    config_data["vm"]["use_sudo"] = True
    config_data["vm"]["sudo_method"] = "su"
    config_data["vm"]["username"] = "kali"
    return Config.from_dict(config_data)


@pytest.fixture
def mock_ssh_result_success() -> CommandResult:
    """Return a successful command result."""
    return CommandResult(
        stdout="Success output",
        stderr="",
        exit_code=0
    )


@pytest.fixture
def mock_ssh_result_failure() -> CommandResult:
    """Return a failed command result."""
    return CommandResult(
        stdout="",
        stderr="Error occurred",
        exit_code=1
    )


@pytest.fixture
def mock_ssh_manager(test_config, mock_ssh_result_success):
    """Return a mocked SSHManager."""
    ssh = MagicMock(spec=SSHManager)
    ssh.config = test_config
    ssh.execute = AsyncMock(return_value=mock_ssh_result_success)
    ssh.connect = AsyncMock()
    ssh.disconnect = AsyncMock()
    ssh._connection = None
    return ssh


@pytest.fixture
def kernel_info_output() -> str:
    """Return sample kernel info output."""
    return """Linux kali 6.1.0-kali5-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.12-1kali2 (2023-02-23) x86_64 GNU/Linux"""


@pytest.fixture
def lsmod_output() -> str:
    """Return sample lsmod output."""
    return """Module                  Size  Used by
mac80211              999424  1 ath9k
cfg80211              933888  2 ath9k,mac80211
rfkill                 28672  3 cfg80211"""


@pytest.fixture
def airmon_output() -> str:
    """Return sample airmon-ng output."""
    return """PHY	Interface	Driver		Chipset

phy0	wlan0		ath9k		Qualcomm Atheros QCA9565

		(mac80211 monitor mode vif enabled for [phy0]wlan0 on [phy0]wlan0mon)
		(mac80211 station mode vif disabled for [phy0]wlan0)"""


@pytest.fixture
def airodump_csv_output() -> str:
    """Return sample airodump-ng CSV output."""
    return """BSSID, First time seen, Last time seen, channel, Speed, Privacy, Cipher, Authentication, Power, # beacons, # IV, LAN IP, ID-length, ESSID, Key
AA:BB:CC:DD:EE:FF, 2024-01-15 10:30:00, 2024-01-15 10:35:00, 6, 54, WPA2, CCMP, PSK, -45, 100, 0, 0.0.0.0, 10, TestNetwork,

Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
"""


@pytest.fixture
def make_output() -> str:
    """Return sample make output."""
    return """make -C /lib/modules/6.1.0-kali5-amd64/build M=/tmp/driver modules
make[1]: Entering directory '/usr/src/linux-headers-6.1.0-kali5-amd64'
  CC [M]  /tmp/driver/my_driver.o
  MODPOST /tmp/driver/Module.symvers
  CC [M]  /tmp/driver/my_driver.mod.o
  LD [M]  /tmp/driver/my_driver.ko
make[1]: Leaving directory '/usr/src/linux-headers-6.1.0-kali5-amd64'"""


@pytest.fixture
def dmesg_output() -> str:
    """Return sample dmesg output."""
    return """[  100.123456] my_driver: loading out-of-tree module
[  100.123789] my_driver: module loaded successfully
[  100.124000] my_driver: device initialized"""
