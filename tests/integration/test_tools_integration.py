"""Integration tests for MCP tools."""

import pytest
import pytest_asyncio
import yaml
from pathlib import Path
from kali_driver_mcp.config import Config
from kali_driver_mcp.ssh_manager import SSHManager
from kali_driver_mcp.tools.kernel_info import get_kernel_info
from kali_driver_mcp.tools.file_ops import get_file_list
from kali_driver_mcp.tools.driver_load import manage_driver
from kali_driver_mcp.tools.log_viewer import view_logs
from kali_driver_mcp.tools.network_info import get_network_info
from kali_driver_mcp.tools.network_monitor import manage_monitor_mode


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
class TestKernelInfoIntegration:
    """Integration tests for kernel info tool."""

    @pytest.mark.asyncio
    async def test_get_kernel_info(self, integration_config, ssh_manager):
        """Test getting kernel information from VM."""
        result = await get_kernel_info(integration_config, ssh_manager)

        assert result["success"] is True
        assert "kernel_version" in result
        assert "Linux" in result["kernel_version"]
        assert "architecture" in result


@pytest.mark.integration
@pytest.mark.requires_vm
class TestFileOperationsIntegration:
    """Integration tests for file operations tool."""

    @pytest.mark.asyncio
    async def test_list_root_directory(self, integration_config, ssh_manager):
        """Test listing root directory."""
        result = await get_file_list(integration_config, ssh_manager, "/")

        assert result["success"] is True
        assert "files" in result
        assert len(result["files"]) > 0

    @pytest.mark.asyncio
    async def test_list_shared_folder(self, integration_config, ssh_manager):
        """Test listing shared folder."""
        vm_path = integration_config.shared_folder.vm_path

        result = await get_file_list(integration_config, ssh_manager, vm_path)

        # Should succeed even if folder is empty
        assert result["success"] is True
        assert "files" in result

    @pytest.mark.asyncio
    async def test_list_nonexistent_path(self, integration_config, ssh_manager):
        """Test listing non-existent path."""
        result = await get_file_list(
            integration_config,
            ssh_manager,
            "/nonexistent/path/12345"
        )

        assert result["success"] is False
        assert "error" in result


@pytest.mark.integration
@pytest.mark.requires_vm
class TestLogViewerIntegration:
    """Integration tests for log viewer tool."""

    @pytest.mark.asyncio
    async def test_view_dmesg(self, integration_config, ssh_manager):
        """Test viewing dmesg logs."""
        result = await view_logs(
            integration_config,
            ssh_manager,
            source="dmesg"
        )

        assert result["success"] is True
        assert "log_lines" in result
        assert len(result["log_lines"]) > 0

    @pytest.mark.asyncio
    async def test_view_dmesg_with_filter(self, integration_config, ssh_manager):
        """Test viewing dmesg logs with filter."""
        result = await view_logs(
            integration_config,
            ssh_manager,
            source="dmesg",
            filter_pattern="kernel"
        )

        assert result["success"] is True
        assert "log_lines" in result

    @pytest.mark.asyncio
    async def test_view_logs_with_lines_limit(self, integration_config, ssh_manager):
        """Test viewing logs with lines limit."""
        result = await view_logs(
            integration_config,
            ssh_manager,
            source="dmesg",
            lines=10
        )

        assert result["success"] is True
        assert len(result["log_lines"]) <= 10


@pytest.mark.integration
@pytest.mark.requires_vm
class TestNetworkInfoIntegration:
    """Integration tests for network info tool."""

    @pytest.mark.asyncio
    async def test_get_network_info(self, integration_config, ssh_manager):
        """Test getting network information."""
        result = await get_network_info(integration_config, ssh_manager)

        assert result["success"] is True
        assert "interfaces" in result
        assert len(result["interfaces"]) > 0

    @pytest.mark.asyncio
    async def test_network_info_has_wireless(self, integration_config, ssh_manager):
        """Test that wireless interface is present."""
        result = await get_network_info(integration_config, ssh_manager)

        assert result["success"] is True

        # Check if configured wireless interface exists
        wireless_iface = integration_config.network.wireless_interface
        interface_names = [iface["name"] for iface in result["interfaces"]]

        # Wireless interface should exist (or monitor mode variant)
        assert any(wireless_iface in name for name in interface_names)


@pytest.mark.integration
@pytest.mark.requires_vm
@pytest.mark.requires_root
@pytest.mark.slow
class TestNetworkMonitorIntegration:
    """Integration tests for network monitor tool."""

    @pytest.mark.asyncio
    async def test_monitor_status(self, integration_config, ssh_manager):
        """Test checking monitor mode status."""
        result = await manage_monitor_mode(
            integration_config,
            ssh_manager,
            "status"
        )

        assert result["success"] is True
        assert "operation" in result
        assert result["operation"] == "status"

    @pytest.mark.asyncio
    async def test_start_stop_monitor_mode(self, integration_config, ssh_manager):
        """Test starting and stopping monitor mode."""
        # First, ensure monitor mode is stopped
        stop_result = await manage_monitor_mode(
            integration_config,
            ssh_manager,
            "stop"
        )
        # OK if it fails (might not be running)

        # Start monitor mode
        start_result = await manage_monitor_mode(
            integration_config,
            ssh_manager,
            "start"
        )

        assert start_result["success"] is True
        assert start_result["operation"] == "start"

        # Stop monitor mode
        stop_result = await manage_monitor_mode(
            integration_config,
            ssh_manager,
            "stop"
        )

        assert stop_result["success"] is True
        assert stop_result["operation"] == "stop"


@pytest.mark.integration
@pytest.mark.requires_vm
@pytest.mark.requires_root
class TestDriverLoadIntegration:
    """Integration tests for driver load/unload."""

    @pytest.mark.asyncio
    async def test_check_loaded_modules(self, integration_config, ssh_manager):
        """Test checking loaded kernel modules."""
        result = await manage_driver(
            integration_config,
            ssh_manager,
            operation="info",
            module_name="cfg80211"  # Common wireless module
        )

        assert result["operation"] == "info"
        # cfg80211 might or might not be loaded

    @pytest.mark.asyncio
    async def test_list_all_modules(self, integration_config, ssh_manager):
        """Test listing all loaded kernel modules."""
        result = await ssh_manager.execute("lsmod")

        assert result.success is True
        assert len(result.stdout) > 0
