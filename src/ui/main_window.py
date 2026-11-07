"""Main application window with complete UI."""

import os
import time
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFileDialog, QMessageBox, QApplication, QFrame
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QIcon, QFontDatabase, QFont

from src.ui.components import (
    Card, SectionHeader, StatusIndicator, PathDisplay,
    IPAddressDisplay, URLDisplay, PrimaryButton, DangerButton,
    SecondaryButton, IconButton, PortSpinBox,
    SelectionInfoWidget
)
from src.ui.styles import get_stylesheet
from src.services.network import (
    detect_wifi_network_info,
    get_wifi_ipv4_address,
    NetworkInfo,
    NetworkStatus,
    NetworkDetectionError,
    is_wifi_available,
)
from src.services.files import (
    FileSelectionInfo,
    SelectionType,
    FileSelectionError,
    get_file_selection_info,
    create_empty_selection,
)
from src.services.server import (
    HTTPServerManager,
    ServerStatus,
    ServerError,
    PortInUseError,
    ServerStartTimeoutError,
)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window for LAN Host."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LAN Host")
        self.resize(950, 720)
        self.setMinimumSize(780, 620)
        self._selection_info: FileSelectionInfo = create_empty_selection()
        self._current_network_info: NetworkInfo | None = None
        self._server_running: bool = False
        self._network_monitor_timer: QTimer | None = None
        self._server_manager = HTTPServerManager(self)
        self._server_manager.statusChanged.connect(self._on_server_status_changed)
        self._setup_ui()
        self._apply_styles()
        self._setup_network_monitoring()
        self._detect_local_ip()

    def _setup_ui(self) -> None:
        """Set up the complete user interface."""
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header
        main_layout.addWidget(self._create_header())

        # Content grid (2 columns)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left column
        left_column = QVBoxLayout()
        left_column.setSpacing(16)
        left_column.addWidget(self._create_host_server_panel())
        left_column.addWidget(self._create_file_selection_panel())
        left_column.addWidget(self._create_sharing_panel())

        # Right column
        right_column = QVBoxLayout()
        right_column.setSpacing(16)
        right_column.addWidget(self._create_network_info_panel())
        right_column.addWidget(self._create_server_settings_panel())
        right_column.addStretch()

        content_layout.addLayout(left_column, 3)
        content_layout.addLayout(right_column, 2)

        main_layout.addLayout(content_layout, 1)

        # Footer
        main_layout.addWidget(self._create_footer())

    def _create_header(self) -> QWidget:
        """Create the application header with logo, title, subtitle and version."""
        header = QWidget()
        header.setObjectName("cardHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # Application logo/icon
        icon_label = QLabel("📡")
        icon_label.setStyleSheet("font-size: 36px;")
        icon_label.setFixedSize(56, 56)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Title and subtitle
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title = QLabel("LAN Host")
        title.setObjectName("titleLabel")
        title_layout.addWidget(title)

        subtitle = QLabel("Host files over your local network")
        subtitle.setObjectName("subtitleLabel")
        title_layout.addWidget(subtitle)

        layout.addLayout(title_layout)
        layout.addStretch()

        # Version badge
        version = QLabel("v1.0.0")
        version.setObjectName("versionLabel")
        version.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(version)

        return header

    def _create_footer(self) -> QWidget:
        """Create the footer with attribution text."""
        footer = QWidget()
        footer.setObjectName("footerWidget")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(0)

        # Add stretch to push text to center
        layout.addStretch()

        footer_text = QLabel("Made by Chaitrangan V Thengekar")
        footer_text.setObjectName("footerLabel")
        footer_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer_text)

        layout.addStretch()

        return footer

    def _create_host_server_panel(self) -> Card:
        """Create the Host Server control panel."""
        card = Card()

        header = SectionHeader("Host Server", "Control the HTTP server")
        card.addWidget(header)

        # Buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        self.host_btn = PrimaryButton("HOST SERVER")
        self.host_btn.setMinimumWidth(180)
        self.host_btn.clicked.connect(self._on_host_clicked)
        buttons_layout.addWidget(self.host_btn)

        self.stop_btn = DangerButton("STOP SERVER")
        self.stop_btn.setMinimumWidth(180)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        buttons_layout.addWidget(self.stop_btn)

        buttons_layout.addStretch()
        card.addLayout(buttons_layout)

        # Status indicator
        status_layout = QHBoxLayout()
        status_layout.setSpacing(12)

        status_label = QLabel("Server Status")
        status_label.setObjectName("sectionSubtitle")
        status_layout.addWidget(status_label)

        self.status_indicator = StatusIndicator()
        status_layout.addWidget(self.status_indicator)

        status_layout.addStretch()
        card.addLayout(status_layout)

        return card

    def _create_file_selection_panel(self) -> Card:
        """Create the file/folder selection panel."""
        card = Card()

        header = SectionHeader("File Selection", "Choose a file or folder to share")
        card.addWidget(header)

        # Browse buttons
        browse_layout = QHBoxLayout()
        browse_layout.setSpacing(12)

        self.browse_folder_btn = SecondaryButton("📁  Browse Folder")
        self.browse_folder_btn.clicked.connect(self._on_browse_folder)
        browse_layout.addWidget(self.browse_folder_btn)

        self.browse_file_btn = SecondaryButton("📄  Browse File")
        self.browse_file_btn.clicked.connect(self._on_browse_file)
        browse_layout.addWidget(self.browse_file_btn)

        self.clear_btn = SecondaryButton("🗑  Clear")
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self._on_clear_selection)
        browse_layout.addWidget(self.clear_btn)

        browse_layout.addStretch()
        card.addLayout(browse_layout)

        # Selection info display (enhanced)
        self.selection_info = SelectionInfoWidget()
        card.addWidget(self.selection_info)

        return card

    def _create_sharing_panel(self) -> Card:
        """Create the sharing URL panel."""
        card = Card()

        header = SectionHeader("Sharing", "Shareable link for other devices")
        card.addWidget(header)

        self.url_display = URLDisplay()
        card.addWidget(self.url_display)

        # Copy button
        copy_layout = QHBoxLayout()
        copy_layout.addStretch()

        self.copy_url_btn = SecondaryButton("📋  Copy URL")
        self.copy_url_btn.setEnabled(False)
        self.copy_url_btn.clicked.connect(self._on_copy_url)
        copy_layout.addWidget(self.copy_url_btn)

        card.addLayout(copy_layout)

        return card

    def _create_network_info_panel(self) -> Card:
        """Create the network information panel."""
        card = Card()

        header = SectionHeader("Network Information", "Your local network details")
        card.addWidget(header)

        # Adapter Name
        adapter_layout = QHBoxLayout()
        adapter_layout.setSpacing(12)

        adapter_label = QLabel("Adapter")
        adapter_label.setObjectName("sectionSubtitle")
        adapter_label.setFixedWidth(100)
        adapter_layout.addWidget(adapter_label)

        self.adapter_display = QLabel("Detecting...")
        self.adapter_display.setObjectName("sectionSubtitle")
        self.adapter_display.setStyleSheet("color: #89b4fa; font-family: 'Consolas', 'Cascadia Code', monospace;")
        adapter_layout.addWidget(self.adapter_display, 1)
        adapter_layout.addStretch()

        card.addLayout(adapter_layout)

        # IPv4 Address
        ip_layout = QHBoxLayout()
        ip_layout.setSpacing(12)

        ip_label = QLabel("IPv4 Address")
        ip_label.setObjectName("sectionSubtitle")
        ip_label.setFixedWidth(100)
        ip_layout.addWidget(ip_label)

        self.ip_display = IPAddressDisplay()
        ip_layout.addWidget(self.ip_display, 1)

        self.refresh_ip_btn = IconButton("↻", "Refresh IP address")
        self.refresh_ip_btn.clicked.connect(self._detect_local_ip)
        ip_layout.addWidget(self.refresh_ip_btn)

        card.addLayout(ip_layout)

        # Connection status
        conn_layout = QHBoxLayout()
        conn_layout.setSpacing(12)

        conn_label = QLabel("Connection")
        conn_label.setObjectName("sectionSubtitle")
        conn_label.setFixedWidth(100)
        conn_layout.addWidget(conn_label)

        self.conn_status = QLabel("Checking...")
        self.conn_status.setObjectName("sectionSubtitle")
        conn_layout.addWidget(self.conn_status)
        conn_layout.addStretch()

        card.addLayout(conn_layout)

        return card

    def _create_server_settings_panel(self) -> Card:
        """Create the server settings panel."""
        card = Card()

        header = SectionHeader("Server Settings", "Configure the HTTP server")
        card.addWidget(header)

        # Port input
        self.port_input = PortSpinBox(default_port=8000)
        self.port_input.valueChanged.connect(self._on_port_changed)
        card.addWidget(self.port_input)

        # Additional settings placeholder
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)

        # Placeholder for future settings
        info_label = QLabel("Additional settings will be available here")
        info_label.setObjectName("placeholderLabel")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(info_label)

        card.addLayout(settings_layout)

        return card

    def _apply_styles(self) -> None:
        """Apply the dark theme stylesheet."""
        self.setStyleSheet(get_stylesheet())

    def _setup_network_monitoring(self) -> None:
        """Set up periodic network monitoring."""
        self._network_monitor_timer = QTimer(self)
        self._network_monitor_timer.setInterval(10000)  # Check every 10 seconds
        self._network_monitor_timer.timeout.connect(self._check_network_changes)
        self._network_monitor_timer.start()

    def _check_network_changes(self) -> None:
        """Check if network interface or IP has changed."""
        try:
            new_info = detect_wifi_network_info()
            if self._current_network_info is None or self._network_info_changed(new_info):
                self._current_network_info = new_info
                self._update_network_display(new_info)
                # Update shareable URL if server is running
                self._update_shareable_url()
        except NetworkDetectionError:
            # Wi-Fi became unavailable
            if self._current_network_info is not None:
                self._current_network_info = None
                self._update_network_display_none()
                self._update_shareable_url()

    def _network_info_changed(self, new_info: NetworkInfo) -> bool:
        """Check if network info has changed significantly."""
        if self._current_network_info is None:
            return True
        return (
            self._current_network_info.ipv4_address != new_info.ipv4_address or
            self._current_network_info.adapter_name != new_info.adapter_name or
            self._current_network_info.status != new_info.status
        )

    def _update_network_display(self, info: NetworkInfo) -> None:
        """Update the network info display with new information."""
        self.ip_display.set_ip(info.ipv4_address)
        self.adapter_display.setText(info.adapter_name)
        
        # Update connection status with color
        if info.status == NetworkStatus.CONNECTED:
            self.conn_status.setText("Connected")
            self.conn_status.setStyleSheet("color: #35D69A;")
        elif info.status == NetworkStatus.DISCONNECTED:
            self.conn_status.setText("Disconnected")
            self.conn_status.setStyleSheet("color: #FF5C68;")
        else:
            self.conn_status.setText("Error")
            self.conn_status.setStyleSheet("color: #FF5C68;")

    def _update_network_display_none(self) -> None:
        """Update display when no Wi-Fi network is available."""
        self.ip_display.set_ip("Not connected")
        self.adapter_display.setText("No active Wi-Fi adapter")
        self.conn_status.setText("No active Wi-Fi connection detected.")
        self.conn_status.setStyleSheet("color: #FF5C68;")

    def _update_shareable_url(self) -> None:
        """Update the shareable URL based on current network and server state."""
        server_status = self._server_manager.get_status()
        logger.debug(f"_update_shareable_url called: server_status={server_status}, selection_info={self._selection_info}")
        
        # Only generate URL if server is RUNNING and we have a valid selection
        if (server_status != ServerStatus.RUNNING
            or not self._selection_info.path 
            or self._selection_info.selection_type == SelectionType.NONE):
            logger.debug("Server not running or no valid selection, clearing URL")
            self.url_display.set_url("")
            self.copy_url_btn.setEnabled(False)
            return
        
        # Get the actual server port from the server manager's config
        server_info = self._server_manager.get_server_info()
        actual_port = server_info.config.port if server_info.config else self.port_input.value()
        logger.debug(f"Using port: {actual_port}")
        
        # Get Wi-Fi IPv4 address
        if self._current_network_info and self._current_network_info.is_active:
            ip = self._current_network_info.ipv4_address
            if ip and ip not in ("Not connected", "Detecting...", "No active adapter"):
                url = self._build_url(ip, actual_port)
                logger.debug(f"Generated Wi-Fi URL: {url}")
                self.url_display.set_url(url)
                self.copy_url_btn.setEnabled(True)
                return
        
        # Fallback: try to detect Wi-Fi IP
        wifi_ip = get_wifi_ipv4_address()
        if wifi_ip:
            url = self._build_url(wifi_ip, actual_port)
            logger.debug(f"Generated fallback Wi-Fi URL: {url}")
            self.url_display.set_url(url)
            self.copy_url_btn.setEnabled(True)
            return
        
        # No Wi-Fi network available
        logger.debug("No active Wi-Fi connection detected")
        self.url_display.set_url("No active Wi-Fi connection detected.")
        self.copy_url_btn.setEnabled(False)

    def _build_url(self, ip: str, port: int) -> str:
        """Build shareable URL for given IP and port."""
        if self._selection_info.selection_type == SelectionType.FOLDER:
            return f"http://{ip}:{port}/"
        else:
            filename = os.path.basename(self._selection_info.path)
            return f"http://{ip}:{port}/{filename}"

    def _on_server_status_changed(self, status: ServerStatus, error: str | None) -> None:
        """Handle server status changes from the server manager."""
        # Use QTimer to ensure UI updates happen on the main thread
        QTimer.singleShot(0, lambda: self._handle_server_status_change(status, error))

    def _handle_server_status_change(self, status: ServerStatus, error: str | None) -> None:
        """Handle server status change on the main thread."""
        if status == ServerStatus.RUNNING:
            self._server_running = True
            self._update_server_state()
            self._update_shareable_url()
        elif status == ServerStatus.STOPPED:
            self._server_running = False
            self._update_server_state()
            self._update_shareable_url()
        elif status == ServerStatus.ERROR:
            self._server_running = False
            self._update_server_state()
            self._update_shareable_url()
            if error:
                QMessageBox.critical(self, "Server Error", error)
        elif status == ServerStatus.STARTING:
            self._server_running = True  # Treat starting as running for UI
            self._update_server_state()
        elif status == ServerStatus.STOPPING:
            # Keep _server_running as is during stopping
            self._update_server_state()

    # --- Event Handlers ---

    def _on_host_clicked(self) -> None:
        """Handle Host Server button click."""
        if not self._selection_info.path or self._selection_info.selection_type == SelectionType.NONE:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a file or folder to host first."
            )
            return

        if not self._selection_info.is_readable:
            QMessageBox.warning(
                self,
                "Invalid Selection",
                f"Cannot host: {self._selection_info.error_message}"
            )
            return

        if not self._current_network_info or not self._current_network_info.is_active:
            QMessageBox.warning(
                self,
                "No Wi-Fi Connection",
                "No active Wi-Fi connection detected. Please connect to a Wi-Fi network and try again."
            )
            return

        # Determine the directory to serve
        if self._selection_info.selection_type == SelectionType.FOLDER:
            serve_dir = self._selection_info.path
        else:
            serve_dir = self._selection_info.parent_directory

        port = self.port_input.value()

        # Start server asynchronously (QProcess handles async internally)
        try:
            self._server_manager.start(serve_dir, port)
        except PortInUseError as e:
            QMessageBox.critical(self, "Port In Use", str(e))
        except ServerError as e:
            QMessageBox.critical(self, "Server Error", str(e))

    def _on_stop_clicked(self) -> None:
        """Handle Stop Server button click."""
        self._server_manager.stop()

    def _on_browse_folder(self) -> None:
        """Handle Browse Folder button click."""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setWindowTitle("Select Folder to Host")

        if dialog.exec():
            paths = dialog.selectedFiles()
            if paths:
                self._handle_selection(paths[0], SelectionType.FOLDER)

    def _on_browse_file(self) -> None:
        """Handle Browse File button click."""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setWindowTitle("Select File to Host")

        if dialog.exec():
            paths = dialog.selectedFiles()
            if paths:
                self._handle_selection(paths[0], SelectionType.FILE)

    def _on_clear_selection(self) -> None:
        """Handle Clear Selection button click."""
        self._clear_selection()

    def _handle_selection(self, path: str, selection_type: SelectionType) -> None:
        """Handle file/folder selection with validation."""
        try:
            info = get_file_selection_info(path, selection_type)
            self._selection_info = info
            self.selection_info.set_info(info)
            self.clear_btn.setEnabled(True)
            # Update shareable URL if server is running
            self._update_shareable_url()
        except FileSelectionError as e:
            # Show error but still allow selection with error state
            error_info = FileSelectionInfo(
                path=os.path.abspath(path) if path else "",
                selection_type=selection_type,
                name=os.path.basename(path) if path else "",
                parent_directory=os.path.dirname(os.path.abspath(path)) if path else "",
                size_bytes=None,
                size_formatted=None,
                is_readable=False,
                error_message=str(e)
            )
            self._selection_info = error_info
            self.selection_info.set_info(error_info)
            self.clear_btn.setEnabled(True)
            QMessageBox.warning(self, "Selection Warning", str(e))

    def _clear_selection(self) -> None:
        """Clear the current selection."""
        self._selection_info = create_empty_selection()
        self.selection_info.clear()
        self.clear_btn.setEnabled(False)
        # Update shareable URL if server is running
        self._update_shareable_url()

    def _on_copy_url(self) -> None:
        """Handle Copy URL button click."""
        url = self.url_display.text()
        if url and not url.startswith("Start the server"):
            QApplication.clipboard().setText(url)
            self.copy_url_btn.setText("✓ Copied!")
            QTimer.singleShot(1500, lambda: self.copy_url_btn.setText("📋  Copy URL"))

    def _on_port_changed(self, port: int) -> None:
        """Handle port value change."""
        # Update URL if server is running
        self._update_shareable_url()

    def _detect_local_ip(self) -> None:
        """Detect and display local Wi-Fi IP address using network service."""
        self.ip_display.setText("Detecting...")
        self.adapter_display.setText("Detecting...")
        self.conn_status.setText("Checking...")
        self.refresh_ip_btn.setEnabled(False)

        # Use QTimer to run detection without blocking GUI
        QTimer.singleShot(0, self._perform_ip_detection)

    def _perform_ip_detection(self) -> None:
        """Perform actual Wi-Fi IP detection using network service."""
        try:
            info = detect_wifi_network_info()
            self._current_network_info = info
            self._update_network_display(info)
            # Update shareable URL if server is running
            self._update_shareable_url()
        except NetworkDetectionError as e:
            self._current_network_info = None
            self._update_network_display_none()
            self._update_shareable_url()
            # Optionally show error in status
            self.conn_status.setText(f"Error: {str(e)}")
            self.conn_status.setStyleSheet("color: #FF5C68;")
        finally:
            self.refresh_ip_btn.setEnabled(True)

    def _update_server_state(self) -> None:
        """Update UI based on server running state."""
        status = self._server_manager.get_status()
        
        if status == ServerStatus.RUNNING:
            self.host_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_indicator.set_status("running")
            self.browse_folder_btn.setEnabled(False)
            self.browse_file_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)
            self.port_input.spinbox.setEnabled(False)
        elif status == ServerStatus.STARTING:
            self.host_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_indicator.set_status("starting")
            self.browse_folder_btn.setEnabled(False)
            self.browse_file_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)
            self.port_input.spinbox.setEnabled(False)
        elif status == ServerStatus.STOPPING:
            self.host_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_indicator.set_status("stopping")
            self.browse_folder_btn.setEnabled(False)
            self.browse_file_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)
            self.port_input.spinbox.setEnabled(False)
        elif status == ServerStatus.ERROR:
            self.host_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_indicator.set_status("error")
            self.browse_folder_btn.setEnabled(True)
            self.browse_file_btn.setEnabled(True)
            if (self._selection_info.path 
                and self._selection_info.selection_type != SelectionType.NONE):
                self.clear_btn.setEnabled(True)
            self.port_input.spinbox.setEnabled(True)
        else:  # STOPPED
            self.host_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_indicator.set_status("stopped")
            self.browse_folder_btn.setEnabled(True)
            self.browse_file_btn.setEnabled(True)
            if (self._selection_info.path 
                and self._selection_info.selection_type != SelectionType.NONE):
                self.clear_btn.setEnabled(True)
            self.port_input.spinbox.setEnabled(True)

    def closeEvent(self, event) -> None:
        """Handle application close event."""
        # Stop server if running
        if self._server_manager.get_status() != ServerStatus.STOPPED:
            self._server_manager.shutdown()
        
        # Stop network monitoring timer
        if self._network_monitor_timer:
            self._network_monitor_timer.stop()
        
        super().closeEvent(event)