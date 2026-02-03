"""Unit tests for configuration management."""

import pytest
from pathlib import Path
from kali_driver_mcp.config import Config, VMConfig, SharedFolderConfig, BuildConfig


def test_config_load_from_dict(test_config_data):
    """Test loading configuration from dictionary."""
    config = Config.from_dict(test_config_data)

    assert config.vm.host == "192.168.2.104"
    assert config.vm.port == 22
    assert config.vm.username == "kali"
    assert config.vm.auth_method == "password"
    assert config.vm.use_sudo is True


def test_vm_config_root_user(test_config_data):
    """Test VM configuration with root user."""
    config_data = test_config_data.copy()
    config_data["vm"]["username"] = "root"
    config_data["vm"]["use_sudo"] = False
    config_data["vm"]["auth_method"] = "key"
    config_data["vm"]["key_file"] = "~/.ssh/kali_vm"

    config = Config.from_dict(config_data)

    assert config.vm.username == "root"
    assert config.vm.use_sudo is False
    assert config.vm.sudo_method == "su"
    assert config.vm.sudo_password is not None


def test_vm_config_with_sudo(test_config_with_sudo):
    """Test VM configuration with sudo enabled."""
    config = test_config_with_sudo

    assert config.vm.username == "kali"
    assert config.vm.use_sudo is True
    assert config.vm.sudo_method == "su"


def test_vm_config_sudo_command_method(test_config_data):
    """Test VM configuration with sudo command method."""
    config_data = test_config_data.copy()
    config_data["vm"]["use_sudo"] = True
    config_data["vm"]["sudo_method"] = "command"
    config_data["vm"]["username"] = "kali"

    config = Config.from_dict(config_data)

    assert config.vm.use_sudo is True
    assert config.vm.sudo_method == "command"


def test_shared_folder_config(test_config):
    """Test shared folder configuration."""
    assert test_config.shared_folder.host_path == "/Users/haoyang/src/AIC8800-Linux-Driver"
    assert test_config.shared_folder.vm_path == "/home/kali/Desktop/share/AIC8800-Linux-Driver"
    assert test_config.shared_folder.verify_mount is True


def test_build_config(test_config):
    """Test build configuration."""
    assert test_config.build.make_jobs == 4
    assert test_config.build.clean_before_build is False


def test_network_config(test_config):
    """Test network configuration."""
    assert test_config.network.wireless_interface == "wlan0"
    assert test_config.network.monitor_interface == "wlan0mon"
    assert test_config.network.default_channel == 6
    assert test_config.network.kill_processes is True


def test_capture_config(test_config):
    """Test capture configuration."""
    assert test_config.capture.output_dir == "/tmp/captures"
    assert test_config.capture.default_duration == 60
    assert test_config.capture.output_format == "pcap,csv"
    assert test_config.capture.update_interval == 1
    assert test_config.capture.band == "bg"


def test_logging_config(test_config):
    """Test logging configuration."""
    assert test_config.logging.max_lines == 1000
    assert test_config.logging.default_source == "dmesg"
    assert test_config.logging.level == "INFO"
    assert test_config.logging.log_commands is True
    assert test_config.logging.log_tools is True


def test_config_defaults():
    """Test configuration defaults."""
    minimal_config = {
        "vm": {
            "host": "192.168.1.100",
            "username": "root",
            "auth_method": "key",
            "key_file": "~/.ssh/id_rsa"
        },
        "shared_folder": {
            "vm_path": "/tmp/share"
        }
    }

    config = Config.from_dict(minimal_config)

    # Check defaults
    assert config.vm.port == 22
    assert config.vm.auth_method == "key"
    assert config.vm.use_sudo is False


def test_config_password_auth(test_config_data):
    """Test configuration with password authentication."""
    config_data = test_config_data.copy()
    config_data["vm"]["auth_method"] = "password"
    config_data["vm"]["password"] = "test-password"

    config = Config.from_dict(config_data)

    assert config.vm.auth_method == "password"
    assert config.vm.password == "test-password"


def test_config_sudo_with_password(test_config_data):
    """Test configuration with sudo password."""
    config_data = test_config_data.copy()
    config_data["vm"]["use_sudo"] = True
    config_data["vm"]["sudo_password"] = "sudo-pass"

    config = Config.from_dict(config_data)

    assert config.vm.use_sudo is True
    assert config.vm.sudo_password == "sudo-pass"
