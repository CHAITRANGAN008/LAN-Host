"""Services module - Contains background services (HTTP server, network discovery)."""

from src.services.network import (
    NetworkInfo,
    ConnectionType,
    NetworkStatus,
    NetworkDetectionError,
    detect_wifi_network_info,
    get_wifi_ipv4_address,
    is_wifi_available,
    is_valid_private_ipv4,
)
from src.services.files import (
    FileSelectionInfo,
    SelectionType,
    FileSelectionError,
    get_file_selection_info,
    create_empty_selection,
    validate_path,
    is_protected_path,
    format_size,
)
from src.services.server import (
    HTTPServerManager,
    ServerConfig,
    ServerInfo,
    ServerStatus,
    ServerError,
    PortInUseError,
    ServerStartTimeoutError,
    is_port_available,
)

__all__ = [
    "NetworkInfo",
    "ConnectionType",
    "NetworkStatus",
    "NetworkDetectionError",
    "detect_wifi_network_info",
    "get_wifi_ipv4_address",
    "is_wifi_available",
    "is_valid_private_ipv4",
    "FileSelectionInfo",
    "SelectionType",
    "FileSelectionError",
    "get_file_selection_info",
    "create_empty_selection",
    "validate_path",
    "is_protected_path",
    "format_size",
    "HTTPServerManager",
    "ServerConfig",
    "ServerInfo",
    "ServerStatus",
    "ServerError",
    "PortInUseError",
    "ServerStartTimeoutError",
    "is_port_available",
]