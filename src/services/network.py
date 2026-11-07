"""Network detection service for LAN Host - Wi-Fi only."""

import socket
import subprocess
import psutil
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ConnectionType(Enum):
    """Network connection type."""
    WIFI = "Wi-Fi"
    ETHERNET = "Ethernet"
    UNKNOWN = "Unknown"


class NetworkStatus(Enum):
    """Network connection status."""
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    NO_NETWORK = "No Network"
    ERROR = "Error"


@dataclass(frozen=True)
class NetworkInfo:
    """Network interface information."""
    ipv4_address: str
    adapter_name: str
    connection_type: ConnectionType
    status: NetworkStatus
    is_active: bool

    def __str__(self) -> str:
        return f"{self.adapter_name} ({self.connection_type.value}): {self.ipv4_address}"


class NetworkDetectionError(Exception):
    """Exception raised when network detection fails."""
    pass


def is_valid_private_ipv4(ip: str) -> bool:
    """
    Check if IPv4 address is a valid private address.
    
    Excludes:
    - 169.254.0.0/16 (APIPA/link-local)
    - 127.0.0.0/8 (loopback)
    - 0.0.0.0
    - Invalid addresses
    
    Accepts:
    - 192.168.x.x (Class C private)
    - 10.x.x.x (Class A private)
    - 172.16.x.x through 172.31.x.x (Class B private)
    """
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        octets = [int(p) for p in parts]
        
        # Exclude loopback
        if octets[0] == 127:
            return False
        
        # Exclude 0.0.0.0
        if ip == "0.0.0.0":
            return False
        
        # Exclude APIPA/link-local (169.254.0.0/16)
        if octets[0] == 169 and octets[1] == 254:
            return False
        
        # Check private ranges
        # 10.0.0.0/8
        if octets[0] == 10:
            return True
        
        # 192.168.0.0/16
        if octets[0] == 192 and octets[1] == 168:
            return True
        
        # 172.16.0.0/12 (172.16.x.x through 172.31.x.x)
        if octets[0] == 172 and 16 <= octets[1] <= 31:
            return True
        
        return False
    except (ValueError, IndexError):
        return False


def _parse_link_speed(speed_str) -> int:
    """Parse link speed string (e.g., '144.4 Mbps', '1 Gbps') to integer bps."""
    if not speed_str:
        return 0
    try:
        if isinstance(speed_str, (int, float)):
            return int(speed_str)
        speed_str = str(speed_str).strip().lower()
        if 'gbps' in speed_str:
            return int(float(speed_str.replace('gbps', '').strip()) * 1_000_000_000)
        elif 'mbps' in speed_str:
            return int(float(speed_str.replace('mbps', '').strip()) * 1_000_000)
        elif 'kbps' in speed_str:
            return int(float(speed_str.replace('kbps', '').strip()) * 1_000)
        else:
            return int(float(speed_str))
    except (ValueError, AttributeError):
        return 0


def get_windows_interface_details() -> dict:
    """
    Get detailed Windows network interface information using PowerShell.
    
    Returns dict mapping interface name to details dict with:
    - name: interface name
    - description: adapter description
    - physical_address: MAC address
    - operational_status: Up/Down/Testing/Dormant/NotPresent/LowerLayerDown
    - interface_type: 71 (Wi-Fi), 6 (Ethernet), etc.
    - if_index: interface index
    """
    try:
        ps_cmd = (
            "Get-NetAdapter | "
            "Select-Object Name, InterfaceDescription, MacAddress, "
            "Status, LinkSpeed, ifIndex, InterfaceType | "
            "ConvertTo-Json"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return {}
        
        import json
        adapters = json.loads(result.stdout)
        
        # Handle single adapter case
        if isinstance(adapters, dict):
            adapters = [adapters]
        
        details = {}
        for adapter in adapters:
            name = adapter.get("Name", "")
            if name:
                details[name] = {
                    "description": adapter.get("InterfaceDescription", ""),
                    "physical_address": adapter.get("MacAddress", ""),
                    "operational_status": adapter.get("Status", ""),
                    "link_speed": adapter.get("LinkSpeed", 0),
                    "interface_type": adapter.get("InterfaceType", 0),
                    "if_index": adapter.get("ifIndex", 0),
                }
        return details
    except Exception:
        return {}


def get_default_gateway_interface() -> Optional[str]:
    """
    Get the network interface associated with the default IPv4 route.
    
    On Windows, this uses the route table to find the interface used for
    the default gateway (0.0.0.0/0).
    
    Returns:
        The interface name (GUID or friendly name) or None if not found.
    """
    try:
        result = subprocess.run(
            ["route", "print", "0.0.0.0"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        lines = result.stdout.splitlines()
        for line in lines:
            parts = line.split()
            if len(parts) >= 5 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                iface = parts[-1]
                return iface
    except Exception:
        pass
    return None


def get_interface_by_ipv4(target_ip: str) -> Optional[str]:
    """
    Find the interface name that has the given IPv4 address.
    
    Args:
        target_ip: The IPv4 address to search for.
        
    Returns:
        The interface name or None if not found.
    """
    try:
        interfaces = psutil.net_if_addrs()
        for iface_name, addrs in interfaces.items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address == target_ip:
                    return iface_name
    except Exception:
        pass
    return None


def get_active_wifi_adapter() -> Optional[dict]:
    """
    Detect the active physical Wi-Fi adapter with a valid private IPv4 address.
    
    Returns a dict with adapter info or None if no suitable Wi-Fi adapter found.
    """
    # Get Windows adapter details
    win_adapters = get_windows_interface_details()
    
    # Get all IPv4 addresses from psutil
    psutil_addrs = psutil.net_if_addrs()
    psutil_stats = psutil.net_if_stats()
    
    # Get default gateway interface
    default_gw_iface = get_default_gateway_interface()
    
    candidates = []
    
    for iface_name, addrs in psutil_addrs.items():
        # Skip if not in Windows adapter list (likely virtual)
        win_info = win_adapters.get(iface_name)
        if not win_info:
            # Try matching by description or partial name
            for wname, winfo in win_adapters.items():
                if wname.lower() == iface_name.lower() or iface_name.lower() in wname.lower():
                    win_info = winfo
                    break
        
        # Check if this is a Wi-Fi adapter
        is_wifi = False
        if win_info:
            # Check interface type (71 = Wi-Fi/802.11)
            iface_type = win_info.get("interface_type", 0)
            if iface_type == 71:
                is_wifi = True
            # Fallback: check description for Wi-Fi keywords
            desc = win_info.get("description", "").lower()
            if not is_wifi:
                wifi_keywords = ["wi-fi", "wifi", "wireless", "wlan", "802.11"]
                if any(kw in desc for kw in wifi_keywords):
                    is_wifi = True
        else:
            # Fallback: check name for Wi-Fi keywords
            iface_lower = iface_name.lower()
            wifi_keywords = ["wi-fi", "wifi", "wireless", "wlan", "802.11"]
            if any(kw in iface_lower for kw in wifi_keywords):
                is_wifi = True
        
        if not is_wifi:
            continue
        
        # Check operational status
        if win_info:
            status = win_info.get("operational_status", "").lower()
            if status not in ("up", "connected"):
                continue
        
        # Check psutil stats
        if iface_name in psutil_stats:
            iface_stat = psutil_stats[iface_name]
            if not iface_stat.isup:
                continue
        elif win_info:
            status = win_info.get("operational_status", "").lower()
            if status not in ("up", "connected"):
                continue
        
        # Check for valid private IPv4 addresses
        valid_ips = []
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ip = addr.address
                if is_valid_private_ipv4(ip):
                    valid_ips.append(ip)
        
        if not valid_ips:
            continue
        
        # Prefer the IP that matches the default gateway interface
        preferred_ip = None
        if default_gw_iface and default_gw_iface in valid_ips:
            preferred_ip = default_gw_iface
        else:
            preferred_ip = valid_ips[0]
        
        candidates.append({
            "iface_name": iface_name,
            "description": win_info.get("description", "") if win_info else iface_name,
            "ip": preferred_ip,
            "all_ips": valid_ips,
            "is_default_gateway": default_gw_iface == iface_name or default_gw_iface in valid_ips,
            "link_speed": _parse_link_speed(win_info.get("link_speed", 0)) if win_info else 0,
        })
    
    if not candidates:
        return None
    
    # Sort candidates: prefer default gateway, then higher link speed
    candidates.sort(key=lambda c: (not c["is_default_gateway"], -c["link_speed"]))
    
    return candidates[0]


def detect_wifi_network_info() -> NetworkInfo:
    """
    Detect the active Wi-Fi network information.
    
    Returns:
        NetworkInfo object with detected Wi-Fi information.
        
    Raises:
        NetworkDetectionError: If no active Wi-Fi adapter with valid IP is found.
    """
    wifi_adapter = get_active_wifi_adapter()
    
    if not wifi_adapter:
        raise NetworkDetectionError("No active Wi-Fi connection detected.")
    
    ipv4 = wifi_adapter["ip"]
    adapter_name = wifi_adapter["iface_name"]
    description = wifi_adapter["description"]
    
    # Display name: use friendly description if available
    display_name = description if description else adapter_name
    
    return NetworkInfo(
        ipv4_address=ipv4,
        adapter_name=display_name,
        connection_type=ConnectionType.WIFI,
        status=NetworkStatus.CONNECTED,
        is_active=True
    )


def get_wifi_ipv4_address() -> Optional[str]:
    """
    Get the active Wi-Fi IPv4 address only.
    
    Returns:
        The Wi-Fi IPv4 address or None if not found.
    """
    try:
        info = detect_wifi_network_info()
        return info.ipv4_address
    except NetworkDetectionError:
        return None


def is_wifi_available() -> bool:
    """
    Quick check if Wi-Fi network is available with valid IP.
    
    Returns:
        True if active Wi-Fi with valid private IPv4 exists.
    """
    try:
        return get_wifi_ipv4_address() is not None
    except Exception:
        return False