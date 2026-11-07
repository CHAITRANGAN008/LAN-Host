"""HTTP server management service for LAN Host using QProcess."""

import os
import sys
import socket
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Callable

from PySide6.QtCore import QProcess, QObject, QTimer, Signal, Slot


logger = logging.getLogger(__name__)


class ServerStatus(Enum):
    """HTTP server status."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass(frozen=True)
class ServerConfig:
    """Configuration for the HTTP server."""
    host: str = "0.0.0.0"
    port: int = 8000
    directory: str = ""


@dataclass
class ServerInfo:
    """Runtime information about the HTTP server."""
    config: ServerConfig
    status: ServerStatus = ServerStatus.STOPPED
    process: Optional[QProcess] = None
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    pid: Optional[int] = None


class ServerError(Exception):
    """Exception raised when server operations fail."""
    pass


class PortInUseError(ServerError):
    """Exception raised when port is already in use."""
    pass


class ServerStartTimeoutError(ServerError):
    """Exception raised when server fails to start within timeout."""
    pass


def is_port_available(host: str, port: int) -> bool:
    """
    Check if a port is available for binding.
    
    Args:
        host: Host address to check.
        port: Port number to check.
        
    Returns:
        True if port is available, False otherwise.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False


def get_python_executable() -> str:
    """Get the current Python executable path."""
    return sys.executable


class HTTPServerManager(QObject):
    """Manages the lifecycle of the Python HTTP server using QProcess."""
    
    # Signals
    statusChanged = Signal(ServerStatus, str)  # status, error_message
    outputReceived = Signal(str)  # stdout line
    errorReceived = Signal(str)   # stderr line
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._server_info = ServerInfo(config=ServerConfig())
        self._process: Optional[QProcess] = None
        self._port_check_timer: Optional[QTimer] = None
        self._port_check_port: int = 0
        self._startup_timeout: int = 15000  # 15 seconds
        self._start_time: float = 0.0
        self._process_started: bool = False
        self._server_ready_detected: bool = False
        
        # Port check timer
        self._port_check_timer = QTimer(self)
        self._port_check_timer.setInterval(200)  # Check every 200ms
        self._port_check_timer.timeout.connect(self._check_port_ready)
    
    def get_server_info(self) -> ServerInfo:
        """Get current server information."""
        return self._server_info
    
    def get_status(self) -> ServerStatus:
        """Get current server status."""
        return self._server_info.status
    
    def is_running(self) -> bool:
        """Check if server is currently running."""
        return self._server_info.status == ServerStatus.RUNNING
    
    def start(self, directory: str, port: int, host: str = "0.0.0.0") -> None:
        """
        Start the HTTP server asynchronously.
        
        Args:
            directory: Directory to serve.
            port: Port to bind to.
            host: Host address to bind to.
            
        Raises:
            ServerError: If server cannot be started (validation errors).
            PortInUseError: If port is already in use.
        """
        if self._server_info.status in (ServerStatus.STARTING, ServerStatus.RUNNING):
            raise ServerError("Server is already running or starting")
        
        # Validate directory
        abs_directory = os.path.abspath(directory)
        if not os.path.isdir(abs_directory):
            raise ServerError(f"Directory does not exist: {abs_directory}")
        
        if not os.access(abs_directory, os.R_OK):
            raise ServerError(f"Permission denied: cannot read {abs_directory}")
        
        # Check port availability
        if not is_port_available(host, port):
            raise PortInUseError(f"Port {port} is already in use on {host}")
        
        # Update config
        config = ServerConfig(host=host, port=port, directory=abs_directory)
        
        # Build command
        python_exe = get_python_executable()
        cmd = [
            python_exe, "-u", "-m", "http.server",
            "--bind", host,
            str(port)
        ]
        
        logger.debug(f"Starting HTTP server:")
        logger.debug(f"  Executable: {python_exe}")
        logger.debug(f"  Working directory: {abs_directory}")
        logger.debug(f"  Command: {' '.join(cmd)}")
        logger.debug(f"  Bind host: {host}, Port: {port}")
        
        # Create QProcess
        self._process = QProcess(self)
        self._process.setWorkingDirectory(abs_directory)
        self._process.setProgram(cmd[0])
        self._process.setArguments(cmd[1:])
        
        # Connect signals
        self._process.started.connect(self._on_process_started)
        self._process.finished.connect(self._on_process_finished)
        self._process.errorOccurred.connect(self._on_process_error)
        self._process.readyReadStandardOutput.connect(self._on_stdout_ready)
        self._process.readyReadStandardError.connect(self._on_stderr_ready)
        
        # Update status to STARTING
        self._update_status(ServerStatus.STARTING)
        self._process_started = False
        
        # Start the process
        self._process.start()
    
    def stop(self) -> None:
        """Stop the HTTP server gracefully."""
        if self._server_info.status == ServerStatus.STOPPED:
            return
        
        if self._server_info.status == ServerStatus.STOPPING:
            return  # Already stopping
        
        self._update_status(ServerStatus.STOPPING)
        
        if self._process is None:
            self._update_status(ServerStatus.STOPPED)
            return
        
        # Stop port checking
        if self._port_check_timer:
            self._port_check_timer.stop()
        
        # Try graceful termination
        self._process.terminate()
        
        # Set up force kill timer
        QTimer.singleShot(5000, self._force_kill_if_needed)
    
    @Slot()
    def _on_process_started(self) -> None:
        """Called when process has started."""
        self._process_started = True
        logger.debug(f"Process started signal received, PID: {self._process.processId() if self._process else 'unknown'}")
        
        if self._process:
            self._server_info = ServerInfo(
                config=self._server_info.config,
                status=ServerStatus.STARTING,
                process=self._process,
                start_time=time.time(),
                pid=self._process.processId()
            )
        
        # Start port checking AFTER process has started
        if self._port_check_timer and not self._port_check_timer.isActive():
            self._start_time = time.time()
            self._port_check_timer.start()
    
    @Slot(int, QProcess.ExitStatus)
    def _on_process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        """Called when process finishes."""
        logger.debug(f"Process finished: exit_code={exit_code}, exit_status={exit_status}")
        
        # Stop port checking
        if self._port_check_timer:
            self._port_check_timer.stop()
        
        # Read any remaining stderr
        stderr = ""
        if self._process:
            stderr_data = self._process.readAllStandardError()
            if stderr_data:
                stderr = stderr_data.data().decode('utf-8', errors='replace')
                logger.debug(f"Process stderr: {stderr}")
        
        was_running = self._server_info.status == ServerStatus.RUNNING
        
        if self._server_info.status == ServerStatus.STOPPING:
            # Graceful stop requested
            logger.info("Server stopped gracefully")
            self._update_status(ServerStatus.STOPPED)
        elif self._server_info.status == ServerStatus.STARTING:
            # Process died during startup
            error_msg = f"Server process exited during startup (code: {exit_code})"
            if stderr:
                error_msg += f"\nStderr: {stderr}"
                logger.error(f"Startup failed: {error_msg}")
            else:
                logger.error(f"Startup failed: {error_msg} (no stderr output)")
            self._update_status(ServerStatus.ERROR, error_msg)
        elif was_running:
            # Process crashed unexpectedly
            error_msg = f"Server process exited unexpectedly (code: {exit_code})"
            if stderr:
                error_msg += f"\nStderr: {stderr}"
                logger.error(f"Unexpected exit: {error_msg}")
            else:
                logger.error(f"Unexpected exit: {error_msg} (no stderr output)")
            self._update_status(ServerStatus.ERROR, error_msg)
        else:
            self._update_status(ServerStatus.STOPPED)
        
        self._process = None
        self._process_started = False
    
    @Slot(QProcess.ProcessError)
    def _on_process_error(self, error: QProcess.ProcessError) -> None:
        """Called when process error occurs."""
        error_messages = {
            QProcess.ProcessError.FailedToStart: "Failed to start server process",
            QProcess.ProcessError.Crashed: "Server process crashed",
            QProcess.ProcessError.Timedout: "Server process timed out",
            QProcess.ProcessError.WriteError: "Error writing to server process",
            QProcess.ProcessError.ReadError: "Error reading from server process",
            QProcess.ProcessError.UnknownError: "Unknown server process error",
        }
        error_msg = error_messages.get(error, f"Server process error: {error}")
        logger.error(f"Process error: {error_msg} (error code: {error})")
        
        # Stop port checking
        if self._port_check_timer:
            self._port_check_timer.stop()
        
        self._update_status(ServerStatus.ERROR, error_msg)
    
    @Slot()
    def _on_stdout_ready(self) -> None:
        """Read stdout from server process."""
        if self._process:
            data = self._process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            for line in data.splitlines():
                if line:
                    logger.debug(f"Server stdout: {line}")
                    self.outputReceived.emit(line)
                    # Detect server ready message
                    if "Serving HTTP on" in line and "port" in line:
                        logger.info(f"Server ready detected from stdout: {line.strip()}")
                        self._server_ready_detected = True
    
    @Slot()
    def _on_stderr_ready(self) -> None:
        """Read stderr from server process."""
        if self._process:
            data = self._process.readAllStandardError().data().decode('utf-8', errors='replace')
            for line in data.splitlines():
                if line:
                    logger.warning(f"Server stderr: {line}")
                    self.errorReceived.emit(line)
    
    def _check_port_ready(self) -> None:
        """Check if server port is accepting connections."""
        if self._server_info.status != ServerStatus.STARTING:
            return
        
        # Check timeout
        if time.time() - self._start_time > self._startup_timeout / 1000.0:
            logger.error(f"Server startup timeout after {self._startup_timeout/1000}s")
            self._port_check_timer.stop()
            self.stop()  # This will trigger _on_process_finished with error
            self._update_status(ServerStatus.ERROR, "Server startup timeout")
            return
        
        # Check if server is ready by looking for the "Serving HTTP" message in stdout
        # This is more reliable than socket connection on Windows
        if self._server_ready_detected:
            logger.info("HTTP server ready (detected via stdout)")
            self._port_check_timer.stop()
            self._update_status(ServerStatus.RUNNING)
            return
        
        # Also try socket connection as fallback (in a separate thread)
        import threading
        def check_port():
            test_hosts = ["127.0.0.1"]
            
            # Also try to get LAN IPs from network interfaces
            try:
                import psutil
                interfaces = psutil.net_if_addrs()
                for iface_name, addrs in interfaces.items():
                    for addr in addrs:
                        if addr.family == socket.AF_INET:
                            ip = addr.address
                            if ip not in ("127.0.0.1", "0.0.0.0"):
                                test_hosts.append(ip)
            except Exception:
                pass
            
            for test_host in test_hosts:
                try:
                    with socket.create_connection((test_host, self._port_check_port), timeout=2.0):
                        # Port is ready - HTTP server is accepting connections
                        logger.info(f"HTTP server ready on port {self._port_check_port} via {test_host}")
                        # Use QTimer to update status on main thread
                        QTimer.singleShot(0, lambda: self._on_port_ready())
                        return
                except (ConnectionRefusedError, OSError, TimeoutError) as e:
                    logger.debug(f"Port check failed for {test_host}: {type(e).__name__}: {e}")
                    continue
            
            # Port not ready yet
        
        threading.Thread(target=check_port, daemon=True).start()

    @Slot()
    def _on_port_ready(self) -> None:
        """Called when port is ready (from port check thread)."""
        if self._server_info.status == ServerStatus.STARTING:
            logger.info("Port ready detected, updating status to RUNNING")
            self._port_check_timer.stop()
            self._update_status(ServerStatus.RUNNING)

    def _force_kill_if_needed(self) -> None:
        """Force kill process if it hasn't stopped yet."""
        if self._process and self._server_info.status == ServerStatus.STOPPING:
            logger.warning("Force killing server process")
            self._process.kill()
    
    def _update_status(self, status: ServerStatus, error: Optional[str] = None) -> None:
        """Update server status and emit signal."""
        self._server_info = ServerInfo(
            config=self._server_info.config,
            status=status,
            process=self._process,
            error_message=error,
            start_time=self._server_info.start_time,
            pid=self._server_info.pid
        )
        logger.debug(f"Status changed to: {status.value}" + (f" - {error}" if error else ""))
        self.statusChanged.emit(status, error or "")
    
    def shutdown(self) -> None:
        """Shutdown the server manager (call on app exit)."""
        if self._port_check_timer:
            self._port_check_timer.stop()
        if self._process and self._server_info.status != ServerStatus.STOPPED:
            self._process.terminate()
            # Wait briefly for termination
            if not self._process.waitForFinished(1000):
                self._process.kill()
                self._process.waitForFinished(1000)


# Need to import time for the timer
import time