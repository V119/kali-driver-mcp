"""Integration tests for SSH connection."""

import pytest
import pytest_asyncio
import yaml
from pathlib import Path
from kali_driver_mcp.config import Config
from kali_driver_mcp.ssh_manager import SSHManager


@pytest.fixture(scope="module")
def integration_config():
    """Load test configuration for integration tests."""
    config_path = Path(__file__).parent.parent / "test_config.yaml"

    if not config_path.exists():
        pytest.skip("test_config.yaml not found - copy from test_config.yaml.example and configure")

    return Config(str(config_path))


@pytest_asyncio.fixture(scope="function")
async def ssh_manager(integration_config):
    """Create and connect SSH manager."""
    ssh = SSHManager(integration_config)
    await ssh.connect()
    yield ssh
    await ssh.close()


@pytest.mark.integration
@pytest.mark.requires_vm
class TestSSHConnection:
    """Integration tests for SSH connection."""

    @pytest.mark.asyncio
    async def test_connect_to_vm(self, integration_config):
        """Test basic SSH connection to VM."""
        ssh = SSHManager(integration_config)

        try:
            await ssh.connect()
            assert ssh._connection is not None
        finally:
            await ssh.close()

    @pytest.mark.asyncio
    async def test_execute_simple_command(self, ssh_manager):
        """Test executing a simple command."""
        result = await ssh_manager.execute("echo 'test'")

        assert result.success is True
        assert result.exit_code == 0
        assert "test" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_whoami(self, ssh_manager, integration_config):
        """Test whoami command to verify user."""
        result = await ssh_manager.execute("whoami")

        assert result.success is True
        assert integration_config.vm.username in result.stdout

    @pytest.mark.asyncio
    async def test_execute_with_sudo(self, ssh_manager, integration_config):
        """Test command execution with sudo if configured."""
        if not integration_config.vm.use_sudo:
            pytest.skip("Sudo not enabled in config")

        result = await ssh_manager.execute("whoami", needs_root=True)

        assert result.success is True
        # When using sudo, whoami should return 'root'
        assert "root" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_uname(self, ssh_manager):
        """Test getting kernel information."""
        result = await ssh_manager.execute("uname -a")

        assert result.success is True
        assert "Linux" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_pwd(self, ssh_manager):
        """Test getting current directory."""
        result = await ssh_manager.execute("pwd")

        assert result.success is True
        assert result.stdout.strip().startswith("/")

    @pytest.mark.asyncio
    async def test_execute_failed_command(self, ssh_manager):
        """Test handling of failed command."""
        result = await ssh_manager.execute("false")

        assert result.success is False
        assert result.exit_code != 0

    @pytest.mark.asyncio
    async def test_execute_nonexistent_command(self, ssh_manager):
        """Test handling of non-existent command."""
        result = await ssh_manager.execute("nonexistent_command_12345")

        assert result.success is False
        assert result.exit_code != 0

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, ssh_manager):
        """Test command timeout handling."""
        result = await ssh_manager.execute("sleep 2", timeout=5)

        # Should complete successfully within timeout
        assert result.success is True

    @pytest.mark.asyncio
    async def test_shared_folder_accessible(self, ssh_manager, integration_config):
        """Test that shared folder is accessible if configured."""
        if not integration_config.shared_folder.verify_mount:
            pytest.skip("Shared folder verification disabled")

        vm_path = integration_config.shared_folder.vm_path
        result = await ssh_manager.execute(f"ls -la {vm_path}")

        assert result.success is True
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_root_privileges(self, ssh_manager, integration_config):
        """Test that we can get root privileges when needed."""
        result = await ssh_manager.execute("id -u", needs_root=True)

        assert result.success is True
        # root user has UID 0
        if integration_config.vm.use_sudo or integration_config.vm.username == "root":
            assert "0" in result.stdout
