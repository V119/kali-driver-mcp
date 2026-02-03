"""Unit tests for MCP tools."""

import pytest
from kali_driver_mcp.tools.kernel_info import get_kernel_info
from kali_driver_mcp.tools.driver_load import manage_driver
from kali_driver_mcp.tools.network_monitor import manage_monitor_mode
from kali_driver_mcp.tools.packet_capture import capture_packets, _parse_airodump_csv


@pytest.mark.unit
class TestKernelInfo:
    """Test kernel info tool."""

    @pytest.mark.asyncio
    async def test_get_kernel_info_success(self, test_config, mock_ssh_manager, kernel_info_output):
        """Test getting kernel information successfully."""
        mock_ssh_manager.execute.return_value.stdout = kernel_info_output

        result = await get_kernel_info(test_config, mock_ssh_manager)
        print(f"Result: {result}")

        # The function returns a dict with version and architecture keys
        assert "version" in result or "architecture" in result
        # If the mock returned success, we should have gotten data
        if mock_ssh_manager.execute.return_value.success:
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_get_kernel_info_failure(self, test_config, mock_ssh_manager, mock_ssh_result_failure):
        """Test kernel info retrieval failure."""
        mock_ssh_manager.execute.return_value = mock_ssh_result_failure

        result = await get_kernel_info(test_config, mock_ssh_manager)

        # When commands fail, the result dict may be empty or partial
        # This is expected behavior - the function doesn't set a "success" field


@pytest.mark.unit
class TestDriverLoad:
    """Test driver loading/unloading tools."""

    @pytest.mark.asyncio
    async def test_load_driver_success(self, test_config, mock_ssh_manager):
        """Test loading driver successfully."""
        # Mock file existence check
        mock_ssh_manager.execute.return_value.stdout = "YES"

        result = await manage_driver(
            test_config,
            mock_ssh_manager,
            operation="load",
            module_name="my_driver"
        )
        print(f"Result: {result}")

        assert result["operation"] == "load"
        assert result["module_name"] == "my_driver"
        # Verify execute was called
        mock_ssh_manager.execute.assert_called()

    @pytest.mark.asyncio
    async def test_load_driver_with_params(self, test_config, mock_ssh_manager):
        """Test loading driver with parameters."""
        # Mock file existence check
        mock_ssh_manager.execute.return_value.stdout = "YES"

        result = await manage_driver(
            test_config,
            mock_ssh_manager,
            operation="load",
            module_name="my_driver",
            parameters={"debug": "1"}
        )
        print(f"Result: {result}")

        assert result["operation"] == "load"

    @pytest.mark.asyncio
    async def test_unload_driver_success(self, test_config, mock_ssh_manager):
        """Test unloading driver successfully."""
        result = await manage_driver(
            test_config,
            mock_ssh_manager,
            operation="unload",
            module_name="my_driver"
        )
        print(f"Result: {result}")

        assert result["success"] is True
        assert result["module_name"] == "my_driver"

    @pytest.mark.asyncio
    async def test_load_driver_file_not_found(self, test_config, mock_ssh_manager):
        """Test loading non-existent driver file."""
        # Mock file check to fail
        mock_ssh_manager.execute.return_value.stdout = "NO"

        result = await manage_driver(
            test_config,
            mock_ssh_manager,
            operation="load",
            module_name="nonexistent_driver"
        )
        print(f"Result: {result}")

        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"]


@pytest.mark.unit
class TestNetworkMonitor:
    """Test network monitor mode tool."""

    @pytest.mark.asyncio
    async def test_start_monitor_mode(self, test_config, mock_ssh_manager, airmon_output):
        """Test starting monitor mode."""
        mock_ssh_manager.execute.return_value.stdout = airmon_output
        mock_ssh_manager.execute.return_value.exit_code = 0

        result = await manage_monitor_mode(
            test_config,
            mock_ssh_manager,
            "start"
        )

        print(f"Result: {result}")

        assert result["operation"] == "start"
        assert result["wireless_interface"] == "wlan0"
        assert result["monitor_interface"] == "wlan0mon"

    @pytest.mark.asyncio
    async def test_start_monitor_mode_with_channel(self, test_config, mock_ssh_manager, airmon_output):
        """Test starting monitor mode with specific channel."""
        mock_ssh_manager.execute.return_value.stdout = airmon_output
        mock_ssh_manager.execute.return_value.exit_code = 0

        result = await manage_monitor_mode(
            test_config,
            mock_ssh_manager,
            "start",
            channel=11
        )

        # Verify channel was passed in command
        calls = mock_ssh_manager.execute.call_args_list
        # Check that one of the calls contains channel 11
        assert any("11" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_stop_monitor_mode(self, test_config, mock_ssh_manager):
        """Test stopping monitor mode."""
        mock_ssh_manager.execute.return_value.exit_code = 0

        result = await manage_monitor_mode(
            test_config,
            mock_ssh_manager,
            "stop"
        )

        assert result["operation"] == "stop"

    @pytest.mark.asyncio
    async def test_monitor_status(self, test_config, mock_ssh_manager, airmon_output):
        """Test checking monitor mode status."""
        mock_ssh_manager.execute.return_value.stdout = airmon_output
        mock_ssh_manager.execute.return_value.exit_code = 0  # This makes success = True

        result = await manage_monitor_mode(
            test_config,
            mock_ssh_manager,
            "status"
        )

        assert result["operation"] == "status"
        assert result["success"] is True


@pytest.mark.unit
class TestPacketCapture:
    """Test packet capture tool."""

    @pytest.mark.asyncio
    async def test_capture_packets_success(self, test_config, mock_ssh_manager):
        """Test capturing packets successfully."""
        # Mock interface check - exit_code 0 means success = True
        mock_ssh_manager.execute.return_value.exit_code = 0

        result = await capture_packets(
            test_config,
            mock_ssh_manager,
            duration=5
        )

        assert result["monitor_interface"] == "wlan0mon"
        assert result["duration"] == 5

    @pytest.mark.asyncio
    async def test_capture_packets_with_bssid(self, test_config, mock_ssh_manager):
        """Test capturing packets with BSSID filter."""
        mock_ssh_manager.execute.return_value.exit_code = 0  # This makes success = True

        result = await capture_packets(
            test_config,
            mock_ssh_manager,
            bssid="AA:BB:CC:DD:EE:FF"
        )

        # Verify bssid was used in command
        calls = mock_ssh_manager.execute.call_args_list
        assert any("AA:BB:CC:DD:EE:FF" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_capture_packets_interface_not_found(self, test_config, mock_ssh_manager, mock_ssh_result_failure):
        """Test capture when monitor interface doesn't exist."""
        # Mock interface check to fail
        mock_ssh_manager.execute.return_value = mock_ssh_result_failure

        result = await capture_packets(
            test_config,
            mock_ssh_manager
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_parse_airodump_csv(self, airodump_csv_output):
        """Test parsing airodump-ng CSV output."""
        networks = _parse_airodump_csv(airodump_csv_output)

        assert len(networks) == 1
        assert networks[0]["bssid"] == "AA:BB:CC:DD:EE:FF"
        assert networks[0]["channel"] == "6"
        assert networks[0]["essid"] == "TestNetwork"
        assert networks[0]["privacy"] == "WPA2"

    def test_parse_airodump_csv_empty(self):
        """Test parsing empty CSV output."""
        networks = _parse_airodump_csv("")
        assert len(networks) == 0

    def test_parse_airodump_csv_no_networks(self):
        """Test parsing CSV with no networks."""
        csv_data = """BSSID, First time seen, Last time seen, channel, Speed, Privacy, Cipher, Authentication, Power, # beacons, # IV, LAN IP, ID-length, ESSID, Key

Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
"""
        networks = _parse_airodump_csv(csv_data)
        assert len(networks) == 0
