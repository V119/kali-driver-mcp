"""Configuration loading and validation."""

import os
from pathlib import Path
from typing import Any, Optional
import yaml


class ConfigError(Exception):
    """Configuration error."""
    pass


class VMConfig:
    """VM connection configuration."""

    def __init__(self, data: dict):
        self.host: str = data.get("host", "")
        self.port: int = data.get("port", 22)
        self.username: str = data.get("username", "root")
        self.auth_method: str = data.get("auth_method", "key")
        self.key_file: Optional[str] = data.get("key_file")
        self.password: Optional[str] = data.get("password")

        # Sudo configuration
        self.use_sudo: bool = data.get("use_sudo", False)
        self.sudo_password: Optional[str] = data.get("sudo_password")
        self.sudo_method: str = data.get("sudo_method", "command")  # "command" or "su"

        if not self.host:
            raise ConfigError("vm.host is required")

        # If not using direct root login and use_sudo is enabled
        if self.username != "root" and self.use_sudo:
            if self.sudo_method not in ["command", "su"]:
                raise ConfigError("vm.sudo_method must be 'command' or 'su'")

        if self.auth_method not in ["key", "password"]:
            raise ConfigError("vm.auth_method must be 'key' or 'password'")
        if self.auth_method == "key" and not self.key_file:
            raise ConfigError("vm.key_file is required when auth_method is 'key'")
        if self.auth_method == "password" and not self.password:
            raise ConfigError("vm.password is required when auth_method is 'password'")

        # Expand key file path
        if self.key_file:
            self.key_file = os.path.expanduser(self.key_file)


class SharedFolderConfig:
    """Shared folder configuration."""

    def __init__(self, data: dict):
        self.host_path: str = data.get("host_path", "")
        self.vm_path: str = data.get("vm_path", "")
        self.verify_mount: bool = data.get("verify_mount", True)

        if not self.vm_path:
            raise ConfigError("shared_folder.vm_path is required")

        # Expand host path
        if self.host_path:
            self.host_path = os.path.expanduser(self.host_path)


class BuildConfig:
    """Build configuration."""

    def __init__(self, data: dict):
        self.make_jobs: int = data.get("make_jobs", 4)
        self.clean_before_build: bool = data.get("clean_before_build", False)


class NetworkConfig:
    """Network interface configuration."""

    def __init__(self, data: dict):
        self.wireless_interface: str = data.get("wireless_interface", "wlan0")
        self.monitor_interface: str = data.get("monitor_interface", "wlan0mon")
        self.default_channel: int = data.get("default_channel", 6)
        self.kill_processes: bool = data.get("kill_processes", True)


class CaptureConfig:
    """Packet capture configuration."""

    def __init__(self, data: dict):
        self.output_dir: str = data.get("output_dir", "/tmp/captures")
        self.default_duration: int = data.get("default_duration", 60)
        self.output_format: str = data.get("output_format", "pcap,csv")
        self.update_interval: int = data.get("update_interval", 1)
        self.band: str = data.get("band", "bg")

        if self.output_format not in ["pcap", "csv", "pcap,csv"]:
            raise ConfigError("capture.output_format must be 'pcap', 'csv', or 'pcap,csv'")


class LoggingConfig:
    """Logging configuration."""

    def __init__(self, data: dict):
        # Log viewer settings
        self.max_lines: int = data.get("max_lines", 1000)
        self.default_source: str = data.get("default_source", "dmesg")

        # Logging system settings
        self.level: str = data.get("level", "INFO")
        self.file: Optional[str] = data.get("file")
        self.json_format: bool = data.get("json_format", False)
        self.enable_console: bool = data.get("enable_console", True)
        self.log_commands: bool = data.get("log_commands", True)
        self.log_tools: bool = data.get("log_tools", True)

        # Expand log file path if provided
        if self.file:
            self.file = os.path.expanduser(self.file)


class Config:
    """Main configuration object."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path

        if not os.path.exists(config_path):
            raise ConfigError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ConfigError("Configuration file is empty")

        # Load all configuration sections
        self._load_configs(data)

    @classmethod
    def from_dict(cls, data: dict):
        """Create Config from dictionary (for testing)."""
        config = cls.__new__(cls)
        config.config_path = "<dict>"
        config._load_configs(data)
        return config

    def _load_configs(self, data: dict):
        """Load configuration sections from data dictionary."""
        self.vm = VMConfig(data.get("vm", {}))
        self.shared_folder = SharedFolderConfig(data.get("shared_folder", {}))
        self.build = BuildConfig(data.get("build", {}))
        self.network = NetworkConfig(data.get("network", {}))
        self.capture = CaptureConfig(data.get("capture", {}))
        self.logging = LoggingConfig(data.get("logging", {}))


def load_config(config_path: str = "config.yaml") -> Config:
    """Load and validate configuration from file."""
    return Config(config_path)
