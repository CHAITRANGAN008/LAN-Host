"""Unit tests for Wi-Fi network detection service."""

import socket
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.services.network import (
    NetworkInfo,
    ConnectionType,
    NetworkStatus,
    NetworkDetectionError,
    detect_wifi_network_info,
    get_wifi_ipv4_address,
    is_wifi_available,
    is_valid_private_ipv4,
    get_windows_interface_details,
    get_active_wifi_adapter,
    get_default_gateway_interface,
    get_interface_by_ipv4,
)


class TestNetworkInfo:
    """Tests for NetworkInfo dataclass."""

    def test_network_info_creation(self):
        """Test NetworkInfo can be created with all fields."""
        info = NetworkInfo(
            ipv4_address="192.168.1.100",
            adapter_name="Wi-Fi",
            connection_type=ConnectionType.WIFI,
            status=NetworkStatus.CONNECTED,
            is_active=True
        )
        assert info.ipv4_address == "192.168.1.100"
        assert info.adapter_name == "Wi-Fi"
        assert info.connection_type == ConnectionType.WIFI
        assert info.status == NetworkStatus.CONNECTED
        assert info.is_active is True

    def test_network_info_str(self):
        """Test NetworkInfo string representation."""
        info = NetworkInfo(
            ipv4_address="192.168.1.100",
            adapter_name="Wi-Fi",
            connection_type=ConnectionType.WIFI,
            status=NetworkStatus.CONNECTED,
            is_active=True
        )
        assert "Wi-Fi" in str(info)
        assert "192.168.1.100" in str(info)


class TestIsValidPrivateIPv4:
    """Tests for is_valid_private_ipv4 function."""

    def test_valid_private_class_a(self):
        """Test 10.x.x.x addresses are valid."""
        assert is_valid_private_ipv4("10.0.0.1") is True
        assert is_valid_private_ipv4("10.255.255.255") is True
        assert is_valid_private_ipv4("10.1.2.3") is True

    def test_valid_private_class_b(self):
        """Test 172.16.x.x through 172.31.x.x addresses are valid."""
        assert is_valid_private_ipv4("172.16.0.1") is True
        assert is_valid_private_ipv4("172.20.1.1") is True
        assert is_valid_private_ipv4("172.31.255.255") is True

    def test_valid_private_class_c(self):
        """Test 192.168.x.x addresses are valid."""
        assert is_valid_private_ipv4("192.168.0.1") is True
        assert is_valid_private_ipv4("192.168.1.100") is True
        assert is_valid_private_ipv4("192.168.255.255") is True

    def test_invalid_loopback(self):
        """Test 127.x.x.x addresses are excluded."""
        assert is_valid_private_ipv4("127.0.0.1") is False
        assert is_valid_private_ipv4("127.255.255.255") is False

    def test_invalid_zero(self):
        """Test 0.0.0.0 is excluded."""
        assert is_valid_private_ipv4("0.0.0.0") is False

    def test_invalid_apipa(self):
        """Test 169.254.x.x (APIPA) addresses are excluded."""
        assert is_valid_private_ipv4("169.254.0.1") is False
        assert is_valid_private_ipv4("169.254.100.100") is False
        assert is_valid_private_ipv4("169.254.255.255") is False

    def test_invalid_public(self):
        """Test public addresses are excluded."""
        assert is_valid_private_ipv4("8.8.8.8") is False
        assert is_valid_private_ipv4("1.1.1.1") is False
        assert is_valid_private_ipv4("203.0.113.1") is False

    def test_invalid_malformed(self):
        """Test malformed addresses are excluded."""
        assert is_valid_private_ipv4("not.an.ip") is False
        assert is_valid_private_ipv4("192.168") is False
        assert is_valid_private_ipv4("192.168.1.1.1") is False
        assert is_valid_private_ipv4("") is False


class TestGetDefaultGatewayInterface:
    """Tests for get_default_gateway_interface function."""

    @patch("src.services.network.subprocess.run")
    def test_windows_route_print(self, mock_run):
        """Test parsing route print output on Windows."""
        mock_result = Mock()
        mock_result.stdout = """
IPv4 Route Table
===========================================================================
Active Routes:
Network Destination        Netmask          Gateway       Interface  Metric
          0.0.0.0          0.0.0.0      192.168.1.1    192.168.1.100     25
        127.0.0.0        255.0.0.0         On-link         127.0.0.1    331
"""
        mock_run.return_value = mock_result

        result = get_default_gateway_interface()
        # The interface is the last column after splitting (Metric in this format)
        assert result == "25"

    @patch("src.services.network.subprocess.run")
    def test_exception_handled(self, mock_run):
        """Test exception handling."""
        mock_run.side_effect = Exception("Command failed")
        result = get_default_gateway_interface()
        assert result is None


class TestGetInterfaceByIPv4:
    """Tests for get_interface_by_ipv4 function."""

    @patch("src.services.network.psutil.net_if_addrs")
    def test_interface_found(self, mock_net_if_addrs):
        """Test finding interface by IPv4 address."""
        mock_net_if_addrs.return_value = {
            "Wi-Fi": [
                Mock(family=socket.AF_INET, address="192.168.1.100"),
                Mock(family=socket.AF_INET6, address="fe80::1"),
            ],
            "Ethernet": [
                Mock(family=socket.AF_INET, address="10.0.0.50"),
            ],
        }

        result = get_interface_by_ipv4("192.168.1.100")
        assert result == "Wi-Fi"

    @patch("src.services.network.psutil.net_if_addrs")
    def test_interface_not_found(self, mock_net_if_addrs):
        """Test when interface is not found."""
        mock_net_if_addrs.return_value = {
            "Wi-Fi": [Mock(family=socket.AF_INET, address="192.168.1.100")],
        }

        result = get_interface_by_ipv4("10.0.0.1")
        assert result is None

    @patch("src.services.network.psutil.net_if_addrs")
    def test_exception_handled(self, mock_net_if_addrs):
        """Test exception handling."""
        mock_net_if_addrs.side_effect = Exception("psutil error")

        result = get_interface_by_ipv4("192.168.1.100")
        assert result is None


class TestGetWindowsInterfaceDetails:
    """Tests for get_windows_interface_details function."""

    @patch("src.services.network.subprocess.run")
    def test_parses_windows_adapters(self, mock_run):
        """Test parsing Windows Get-NetAdapter output."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''[
            {
                "Name": "Wi-Fi",
                "InterfaceDescription": "Intel(R) Wi-Fi 6 AX201 160MHz",
                "MacAddress": "00-11-22-33-44-55",
                "Status": "Up",
                "LinkSpeed": 866000000,
                "ifIndex": 12,
                "InterfaceType": 71
            },
            {
                "Name": "Ethernet",
                "InterfaceDescription": "Realtek PCIe GBE Family Controller",
                "MacAddress": "AA-BB-CC-DD-EE-FF",
                "Status": "Down",
                "LinkSpeed": 1000000000,
                "ifIndex": 8,
                "InterfaceType": 6
            }
        ]'''
        mock_run.return_value = mock_result

        details = get_windows_interface_details()
        
        assert "Wi-Fi" in details
        assert details["Wi-Fi"]["description"] == "Intel(R) Wi-Fi 6 AX201 160MHz"
        assert details["Wi-Fi"]["interface_type"] == 71
        assert details["Wi-Fi"]["operational_status"] == "Up"
        
        assert "Ethernet" in details
        assert details["Ethernet"]["interface_type"] == 6
        assert details["Ethernet"]["operational_status"] == "Down"

    @patch("src.services.network.subprocess.run")
    def test_single_adapter(self, mock_run):
        """Test parsing single adapter (not in array)."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''{
            "Name": "Wi-Fi",
            "InterfaceDescription": "Intel Wi-Fi",
            "MacAddress": "00-11-22-33-44-55",
            "Status": "Up",
            "LinkSpeed": 866000000,
            "ifIndex": 12,
            "InterfaceType": 71
        }'''
        mock_run.return_value = mock_result

        details = get_windows_interface_details()
        assert "Wi-Fi" in details
        assert details["Wi-Fi"]["interface_type"] == 71


class TestGetActiveWifiAdapter:
    """Tests for get_active_wifi_adapter function."""

    @patch("src.services.network.get_windows_interface_details")
    @patch("src.services.network.psutil.net_if_addrs")
    @patch("src.services.network.psutil.net_if_stats")
    @patch("src.services.network.get_default_gateway_interface")
    def test_finds_active_wifi_with_valid_ip(
        self, mock_gateway, mock_stats, mock_addrs, mock_win_details
    ):
        """Test finding active Wi-Fi adapter with valid private IP."""
        # Mock Windows adapter details
        mock_win_details.return_value = {
            "Wi-Fi": {
                "description": "Intel(R) Wi-Fi 6 AX201 160MHz",
                "physical_address": "00-11-22-33-44-55",
                "operational_status": "Up",
                "link_speed": 866000000,
                "interface_type": 71,
                "if_index": 12,
            },
            "Ethernet": {
                "description": "Realtek PCIe GBE",
                "physical_address": "AA-BB-CC-DD-EE-FF",
                "operational_status": "Down",
                "link_speed": 1000000000,
                "interface_type": 6,
                "if_index": 8,
            }
        }

        # Mock psutil addresses
        mock_addrs.return_value = {
            "Wi-Fi": [
                Mock(family=socket.AF_INET, address="192.168.1.100"),
                Mock(family=socket.AF_INET, address="169.254.1.1"),  # APIPA - should be excluded
                Mock(family=socket.AF_INET6, address="fe80::1"),
            ],
            "Ethernet": [
                Mock(family=socket.AF_INET, address="10.0.0.50"),
            ],
        }

        # Mock psutil stats
        mock_stats.return_value = {
            "Wi-Fi": Mock(isup=True),
            "Ethernet": Mock(isup=False),
        }

        # Mock default gateway
        mock_gateway.return_value = "192.168.1.100"

        adapter = get_active_wifi_adapter()

        assert adapter is not None
        assert adapter["iface_name"] == "Wi-Fi"
        assert adapter["ip"] == "192.168.1.100"
        assert adapter["description"] == "Intel(R) Wi-Fi 6 AX201 160MHz"

    @patch("src.services.network.get_windows_interface_details")
    @patch("src.services.network.psutil.net_if_addrs")
    @patch("src.services.network.psutil.net_if_stats")
    @patch("src.services.network.get_default_gateway_interface")
    def test_excludes_apipa_addresses(
        self, mock_gateway, mock_stats, mock_addrs, mock_win_details
    ):
        """Test that APIPA addresses (169.254.x.x) are excluded."""
        mock_win_details.return_value = {
            "Wi-Fi": {
                "description": "Intel Wi-Fi",
                "operational_status": "Up",
                "link_speed": 866000000,
                "interface_type": 71,
                "if_index": 12,
            }
        }

        mock_addrs.return_value = {
            "Wi-Fi": [
                Mock(family=socket.AF_INET, address="169.254.100.100"),  # APIPA only
                Mock(family=socket.AF_INET6, address="fe80::1"),
            ],
        }

        mock_stats.return_value = {
            "Wi-Fi": Mock(isup=True),
        }

        mock_gateway.return_value = None

        adapter = get_active_wifi_adapter()

        assert adapter is None  # No valid private IP

    @patch("src.services.network.get_windows_interface_details")
    @patch("src.services.network.psutil.net_if_addrs")
    @patch("src.services.network.psutil.net_if_stats")
    @patch("src.services.network.get_default_gateway_interface")
    def test_excludes_loopback(
        self, mock_gateway, mock_stats, mock_addrs, mock_win_details
    ):
        """Test that loopback addresses (127.x.x.x) are excluded."""
        mock_win_details.return_value = {
            "Wi-Fi": {
                "description": "Intel Wi-Fi",
                "operational_status": "Up",
                "link_speed": 866000000,
                "interface_type": 71,
                "if_index": 12,
            }
        }

        mock_addrs.return_value = {
            "Wi-Fi": [
                Mock(family=socket.AF_INET, address="127.0.0.1"),  # Loopback only
            ],
        }

        mock_stats.return_value = {
            "Wi-Fi": Mock(isup=True),
        }

        mock_gateway.return_value = None

        adapter = get_active_wifi_adapter()

        assert adapter is None  # No valid private IP

    @patch("src.services.network.get_windows_interface_details")
    @patch("src.services.network.psutil.net_if_addrs")
    @patch("src.services.network.psutil.net_if_stats")
    @patch("src.services.network.get_default_gateway_interface")
    def test_excludes_down_interface(
        self, mock_gateway, mock_stats, mock_addrs, mock_win_details
    ):
        """Test that down interfaces are excluded."""
        mock_win_details.return_value = {
            "Wi-Fi": {
                "description": "Intel Wi-Fi",
                "operational_status": "Down",  # Not Up
                "link_speed": 866000000,
                "interface_type": 71,
                "if_index": 12,
            }
        }

        mock_addrs.return_value = {
            "Wi-Fi": [
                Mock(family=socket.AF_INET, address="192.168.1.100"),
            ],
        }

        mock_stats.return_value = {
            "Wi-Fi": Mock(isup=False),
        }

        mock_gateway.return_value = None

        adapter = get_active_wifi_adapter()

        assert adapter is None  # Interface is down

    @patch("src.services.network.get_windows_interface_details")
    @patch("src.services.network.psutil.net_if_addrs")
    @patch("src.services.network.psutil.net_if_stats")
    @patch("src.services.network.get_default_gateway_interface")
    def test_excludes_ethernet(
        self, mock_gateway, mock_stats, mock_addrs, mock_win_details
    ):
        """Test that Ethernet adapters are excluded even with valid IP."""
        mock_win_details.return_value = {
            "Ethernet": {
                "description": "Realtek PCIe GBE",
                "operational_status": "Up",
                "link_speed": 1000000000,
                "interface_type": 6,  # Ethernet
                "if_index": 8,
            }
        }

        mock_addrs.return_value = {
            "Ethernet": [
                Mock(family=socket.AF_INET, address="192.168.1.50"),
            ],
        }

        mock_stats.return_value = {
            "Ethernet": Mock(isup=True),
        }

        mock_gateway.return_value = None

        adapter = get_active_wifi_adapter()

        assert adapter is None  # Ethernet should be excluded

    @patch("src.services.network.get_windows_interface_details")
    @patch("src.services.network.psutil.net_if_addrs")
    @patch("src.services.network.psutil.net_if_stats")
    @patch("src.services.network.get_default_gateway_interface")
    def test_prefers_default_gateway(
        self, mock_gateway, mock_stats, mock_addrs, mock_win_details
    ):
        """Test that adapter with default gateway is preferred."""
        mock_win_details.return_value = {
            "Wi-Fi": {
                "description": "Intel Wi-Fi",
                "operational_status": "Up",
                "link_speed": 866000000,
                "interface_type": 71,
                "if_index": 12,
            },
            "Wi-Fi 2": {
                "description": "Virtual Wi-Fi",
                "operational_status": "Up",
                "link_speed": 54000000,
                "interface_type": 71,
                "if_index": 14,
            }
        }

        mock_addrs.return_value = {
            "Wi-Fi": [
                Mock(family=socket.AF_INET, address="192.168.1.100"),
            ],
            "Wi-Fi 2": [
                Mock(family=socket.AF_INET, address="10.0.0.100"),
            ],
        }

        mock_stats.return_value = {
            "Wi-Fi": Mock(isup=True),
            "Wi-Fi 2": Mock(isup=True),
        }

        # Default gateway is on Wi-Fi
        mock_gateway.return_value = "192.168.1.100"

        adapter = get_active_wifi_adapter()

        assert adapter is not None
        assert adapter["iface_name"] == "Wi-Fi"
        assert adapter["ip"] == "192.168.1.100"


class TestDetectWifiNetworkInfo:
    """Tests for detect_wifi_network_info function."""

    @patch("src.services.network.get_active_wifi_adapter")
    def test_successful_detection(self, mock_get_adapter):
        """Test successful Wi-Fi network info detection."""
        mock_get_adapter.return_value = {
            "iface_name": "Wi-Fi",
            "description": "Intel(R) Wi-Fi 6 AX201 160MHz",
            "ip": "192.168.1.100",
            "all_ips": ["192.168.1.100"],
            "is_default_gateway": True,
            "link_speed": 866000000,
        }

        info = detect_wifi_network_info()

        assert info.ipv4_address == "192.168.1.100"
        assert info.adapter_name == "Intel(R) Wi-Fi 6 AX201 160MHz"
        assert info.connection_type == ConnectionType.WIFI
        assert info.status == NetworkStatus.CONNECTED
        assert info.is_active is True

    @patch("src.services.network.get_active_wifi_adapter")
    def test_no_wifi_raises_error(self, mock_get_adapter):
        """Test NetworkDetectionError when no Wi-Fi adapter found."""
        mock_get_adapter.return_value = None

        with pytest.raises(NetworkDetectionError) as exc_info:
            detect_wifi_network_info()

        assert "No active Wi-Fi connection detected" in str(exc_info.value)


class TestGetWifiIpv4Address:
    """Tests for get_wifi_ipv4_address function."""

    @patch("src.services.network.detect_wifi_network_info")
    def test_returns_ip(self, mock_detect):
        """Test returning IPv4 address."""
        mock_detect.return_value = NetworkInfo(
            ipv4_address="192.168.1.100",
            adapter_name="Wi-Fi",
            connection_type=ConnectionType.WIFI,
            status=NetworkStatus.CONNECTED,
            is_active=True
        )

        result = get_wifi_ipv4_address()
        assert result == "192.168.1.100"

    @patch("src.services.network.detect_wifi_network_info")
    def test_returns_none_on_error(self, mock_detect):
        """Test returning None on detection error."""
        mock_detect.side_effect = NetworkDetectionError("No Wi-Fi")

        result = get_wifi_ipv4_address()
        assert result is None


class TestIsWifiAvailable:
    """Tests for is_wifi_available function."""

    @patch("src.services.network.get_wifi_ipv4_address")
    def test_available(self, mock_get_ip):
        """Test Wi-Fi available."""
        mock_get_ip.return_value = "192.168.1.100"
        assert is_wifi_available() is True

    @patch("src.services.network.get_wifi_ipv4_address")
    def test_not_available(self, mock_get_ip):
        """Test Wi-Fi not available."""
        mock_get_ip.return_value = None
        assert is_wifi_available() is False

    @patch("src.services.network.get_wifi_ipv4_address")
    def test_exception_handled(self, mock_get_ip):
        """Test exception handling."""
        mock_get_ip.side_effect = Exception("Error")
        assert is_wifi_available() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])