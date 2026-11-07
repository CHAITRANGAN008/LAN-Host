"""Unit tests for HTTP server service."""

import os
import socket
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.services.server import (
    HTTPServerManager,
    ServerConfig,
    ServerInfo,
    ServerStatus,
    ServerError,
    PortInUseError,
    ServerStartTimeoutError,
    is_port_available,
    get_python_executable,
)


class TestPortAvailability:
    """Tests for port availability checking."""

    def test_port_available(self):
        """Test that an unused port is reported as available."""
        # Use port 0 to let OS assign a free port, then check another
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]
        
        # The port should be available again after socket closes
        assert is_port_available("127.0.0.1", free_port) is True

    def test_port_in_use(self):
        """Test that a port in use is reported as unavailable."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
            s.listen(1)
            assert is_port_available("127.0.0.1", port) is False


class TestGetPythonExecutable:
    """Tests for get_python_executable function."""

    def test_returns_valid_path(self):
        """Test that function returns a valid Python executable path."""
        exe = get_python_executable()
        assert exe is not None
        assert len(exe) > 0
        assert os.path.exists(exe) or "python" in exe.lower()


class TestServerConfig:
    """Tests for ServerConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ServerConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.directory == ""

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ServerConfig(host="127.0.0.1", port=9000, directory="/tmp")
        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.directory == "/tmp"


class TestServerInfo:
    """Tests for ServerInfo dataclass."""

    def test_default_info(self):
        """Test default server info."""
        config = ServerConfig()
        info = ServerInfo(config=config)
        assert info.status == ServerStatus.STOPPED
        assert info.process is None
        assert info.error_message is None
        assert info.start_time is None
        assert info.pid is None

    def test_custom_info(self):
        """Test custom server info."""
        config = ServerConfig(port=8080)
        info = ServerInfo(
            config=config,
            status=ServerStatus.RUNNING,
            error_message="Test error"
        )
        assert info.status == ServerStatus.RUNNING
        assert info.error_message == "Test error"


class TestServerStatus:
    """Tests for ServerStatus enum."""

    def test_all_statuses(self):
        """Test all status enum values."""
        assert ServerStatus.STOPPED.value == "stopped"
        assert ServerStatus.STARTING.value == "starting"
        assert ServerStatus.RUNNING.value == "running"
        assert ServerStatus.STOPPING.value == "stopping"
        assert ServerStatus.ERROR.value == "error"


class TestHTTPServerManager:
    """Tests for HTTPServerManager class (synchronous validation only)."""

    def test_initial_state(self):
        """Test initial state of server manager."""
        manager = HTTPServerManager()
        assert manager.get_status() == ServerStatus.STOPPED
        assert manager.is_running() is False
        info = manager.get_server_info()
        assert info.status == ServerStatus.STOPPED

    def test_start_invalid_directory(self):
        """Test starting with a file instead of directory."""
        manager = HTTPServerManager()
        
        with tempfile.NamedTemporaryFile() as f:
            with pytest.raises(ServerError):
                manager.start(f.name, 8000)
        
        assert manager.get_status() == ServerStatus.STOPPED

    def test_start_nonexistent_directory(self):
        """Test starting with a nonexistent directory."""
        manager = HTTPServerManager()
        
        with pytest.raises(ServerError):
            manager.start("/nonexistent/directory", 8000)
        
        assert manager.get_status() == ServerStatus.STOPPED

    def test_start_port_in_use(self):
        """Test starting on a port that's already in use."""
        manager = HTTPServerManager()
        
        # Create a socket to hold the port on 0.0.0.0 (same as server binds to)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("0.0.0.0", 0))
        port = sock.getsockname()[1]
        sock.listen(1)
        
        try:
            with pytest.raises(PortInUseError):
                manager.start(tempfile.gettempdir(), port)
        finally:
            sock.close()
        
        assert manager.get_status() == ServerStatus.STOPPED

    def test_stop_already_stopped(self):
        """Test stopping an already stopped server."""
        manager = HTTPServerManager()
        # Should not raise
        manager.stop()
        assert manager.get_status() == ServerStatus.STOPPED

    def test_shutdown(self):
        """Test shutdown cleans up properly."""
        manager = HTTPServerManager()
        manager.shutdown()
        assert manager.get_status() == ServerStatus.STOPPED

    def test_signals_exist(self):
        """Test that required signals exist."""
        manager = HTTPServerManager()
        # Verify signals are defined
        assert hasattr(manager, 'statusChanged')
        assert hasattr(manager, 'outputReceived')
        assert hasattr(manager, 'errorReceived')


class TestServerErrors:
    """Tests for server exception classes."""

    def test_server_error(self):
        """Test ServerError exception."""
        with pytest.raises(ServerError):
            raise ServerError("Test error")

    def test_port_in_use_error(self):
        """Test PortInUseError exception."""
        with pytest.raises(PortInUseError):
            raise PortInUseError("Port 8000 in use")

    def test_server_start_timeout_error(self):
        """Test ServerStartTimeoutError exception."""
        with pytest.raises(ServerStartTimeoutError):
            raise ServerStartTimeoutError("Timeout")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])