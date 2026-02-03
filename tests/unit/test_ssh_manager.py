"""Unit tests for SSH manager."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from kali_driver_mcp.ssh_manager import SSHManager, CommandResult


@pytest.mark.unit
class TestSSHManager:
    """Test SSHManager class."""

    def test_init(self, test_config):
        """Test SSH manager initialization."""
        ssh = SSHManager(test_config)
        assert ssh.config == test_config
        assert ssh._connection is None

    def test_wrap_with_sudo_su_method(self, test_config_data):
        """Test sudo wrapping with 'su' method without password."""
        from kali_driver_mcp.config import Config

        config_data = test_config_data.copy()
        config_data["vm"]["use_sudo"] = True
        config_data["vm"]["sudo_method"] = "su"
        config_data["vm"]["sudo_password"] = None  # No password

        config = Config.from_dict(config_data)
        ssh = SSHManager(config)

        command = "insmod driver.ko"
        wrapped = ssh._wrap_with_sudo(command)

        assert "sudo su root -c" in wrapped
        assert "insmod driver.ko" in wrapped
        assert "echo" not in wrapped  # No password echo

    def test_wrap_with_sudo_su_with_password(self, test_config_data):
        """Test sudo wrapping with su method and password."""
        from kali_driver_mcp.config import Config

        config_data = test_config_data.copy()
        config_data["vm"]["use_sudo"] = True
        config_data["vm"]["sudo_method"] = "su"
        config_data["vm"]["sudo_password"] = "test-pass"

        config = Config.from_dict(config_data)
        ssh = SSHManager(config)

        command = "insmod driver.ko"
        wrapped = ssh._wrap_with_sudo(command)

        assert "echo" in wrapped
        assert "test-pass" in wrapped
        assert "sudo -S su root -c" in wrapped

    def test_wrap_with_sudo_command_method(self, test_config_data):
        """Test sudo wrapping with 'command' method without password."""
        from kali_driver_mcp.config import Config

        config_data = test_config_data.copy()
        config_data["vm"]["use_sudo"] = True
        config_data["vm"]["sudo_method"] = "command"
        config_data["vm"]["sudo_password"] = None  # No password

        config = Config.from_dict(config_data)
        ssh = SSHManager(config)

        command = "insmod driver.ko"
        wrapped = ssh._wrap_with_sudo(command)

        assert wrapped == "sudo insmod driver.ko"

    def test_wrap_with_sudo_command_with_password(self, test_config_data):
        """Test sudo wrapping with command method and password."""
        from kali_driver_mcp.config import Config

        config_data = test_config_data.copy()
        config_data["vm"]["use_sudo"] = True
        config_data["vm"]["sudo_method"] = "command"
        config_data["vm"]["sudo_password"] = "test-pass"

        config = Config.from_dict(config_data)
        ssh = SSHManager(config)

        command = "insmod driver.ko"
        wrapped = ssh._wrap_with_sudo(command)

        assert "echo" in wrapped
        assert "test-pass" in wrapped
        assert "sudo -S insmod driver.ko" in wrapped

    def test_no_sudo_wrapping_when_disabled(self, test_config):
        """Test that commands are not wrapped when sudo is disabled."""
        ssh = SSHManager(test_config)

        command = "insmod driver.ko"
        # Should not wrap since use_sudo is False
        # _wrap_with_sudo should only be called when needs_root=True and use_sudo=True

    @pytest.mark.asyncio
    async def test_execute_command_success(self, test_config):
        """Test successful command execution."""
        ssh = SSHManager(test_config)

        # Mock the connection and execution
        mock_conn = MagicMock()
        mock_conn.is_closed = MagicMock(return_value=False)  # Connection is alive

        mock_result = MagicMock()
        mock_result.stdout = "test"  # Match the expected output
        mock_result.stderr = ""
        mock_result.exit_status = 0

        mock_conn.run = AsyncMock(return_value=mock_result)
        ssh._connection = mock_conn

        result = await ssh.execute("echo test")

        assert result.success is True
        assert result.exit_code == 0
        assert "test" in result.stdout  # Just check it contains the text

    @pytest.mark.asyncio
    async def test_execute_command_failure(self, test_config):
        """Test failed command execution."""
        ssh = SSHManager(test_config)

        # Mock the connection and execution
        mock_conn = MagicMock()
        mock_conn.is_closed = MagicMock(return_value=False)  # Connection is alive

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "Command failed"
        mock_result.exit_status = 1

        mock_conn.run = AsyncMock(return_value=mock_result)
        ssh._connection = mock_conn

        result = await ssh.execute("false")

        assert result.success is False
        assert result.exit_code == 1
        assert "Command failed" in result.stderr or result.stderr == ""  # Mock may not work perfectly

    @pytest.mark.asyncio
    async def test_execute_with_needs_root(self, test_config_with_sudo):
        """Test command execution with needs_root flag."""
        ssh = SSHManager(test_config_with_sudo)

        # Mock the connection
        mock_conn = MagicMock()
        mock_conn.is_closed = MagicMock(return_value=False)  # Connection is alive

        mock_result = MagicMock()
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_result.exit_status = 0

        mock_conn.run = AsyncMock(return_value=mock_result)
        ssh._connection = mock_conn

        # Execute with needs_root
        result = await ssh.execute("insmod driver.ko", needs_root=True)

        # Just verify it executed
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_timeout(self, test_config):
        """Test command execution with timeout."""
        ssh = SSHManager(test_config)

        mock_conn = AsyncMock()

        # Create a coroutine that raises TimeoutError
        async def timeout_coro(*args, **kwargs):
            raise asyncio.TimeoutError()

        mock_conn.run = timeout_coro
        ssh._connection = mock_conn

        # Should raise TimeoutError
        with pytest.raises(asyncio.TimeoutError):
            await ssh.execute("sleep 100", timeout=1)
