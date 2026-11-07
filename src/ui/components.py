"""Reusable UI components for LAN Host application."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy,
    QSpinBox, QToolTip
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property, QEvent, QRect
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QFontMetrics, QPainterPath

from src.services.files import FileSelectionInfo, SelectionType


class Card(QFrame):
    """A styled card/panel container with rounded corners and border."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(14)

    def addWidget(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def addLayout(self, layout: QVBoxLayout | QHBoxLayout) -> None:
        self._layout.addLayout(layout)

    def addSpacing(self, space: int) -> None:
        self._layout.addSpacing(space)

    def addStretch(self, stretch: int = 1) -> None:
        self._layout.addStretch(stretch)


class SectionHeader(QWidget):
    """Section header with title and optional subtitle."""

    def __init__(
        self,
        title: str,
        subtitle: str | None = None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("cardHeader")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("sectionTitle")
        layout.addWidget(self.title_label)

        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setObjectName("sectionSubtitle")
            layout.addWidget(self.subtitle_label)


class StatusIndicator(QWidget):
    """Premium status indicator with colored dot and text."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("statusIndicator")
        self.setFixedHeight(36)
        self._status = "stopped"
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Status dot (will be painted)
        self.dot_widget = _StatusDot()
        self.dot_widget.setFixedSize(10, 10)
        layout.addWidget(self.dot_widget)

        # Status text
        self.text_label = QLabel("NOT RUNNING")
        self.text_label.setObjectName("statusText")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.text_label.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        layout.addWidget(self.text_label)

    def set_status(self, status: str) -> None:
        """Set status: 'running', 'stopped', 'starting', 'stopping', or 'error'."""
        self._status = status
        self.dot_widget.set_status(status)
        
        if status == "running":
            self.text_label.setText("RUNNING")
        elif status == "starting":
            self.text_label.setText("STARTING...")
        elif status == "stopping":
            self.text_label.setText("STOPPING...")
        elif status == "error":
            self.text_label.setText("ERROR")
        else:
            self.text_label.setText("NOT RUNNING")


class _StatusDot(QWidget):
    """Animated colored status dot."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._status = "stopped"
        self._pulse = 0.0
        self._animation = QPropertyAnimation(self, b"pulse", self)
        self._animation.setDuration(1000)
        self._animation.setLoopCount(-1)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        
    def set_status(self, status: str) -> None:
        self._status = status
        if status in ("running", "starting"):
            self._animation.setStartValue(0.0)
            self._animation.setEndValue(1.0)
            self._animation.start()
        else:
            self._animation.stop()
            self._pulse = 0.0
        self.update()
    
    def _get_pulse(self) -> float:
        return self._pulse
    
    def _set_pulse(self, value: float) -> None:
        self._pulse = value
        self.update()
    
    pulse = Property(float, _get_pulse, _set_pulse)
    
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2
        
        # Colors based on status
        if self._status == "running":
            color = QColor("#35D69A")
            pulse_color = QColor("#35D69A")
        elif self._status == "starting":
            color = QColor("#5798FF")
            pulse_color = QColor("#5798FF")
        elif self._status == "stopping":
            color = QColor("#FFA500")
            pulse_color = QColor("#FFA500")
        elif self._status == "error":
            color = QColor("#FF5C68")
            pulse_color = QColor("#FF5C68")
        else:  # stopped
            color = QColor("#FF5C68")
            pulse_color = QColor("#FF5C68")
        
        # Draw pulse ring for active states
        if self._status in ("running", "starting") and self._pulse > 0:
            pulse_radius = radius + int(6 * self._pulse)
            pulse_alpha = int(100 * (1.0 - self._pulse))
            pulse_color.setAlpha(pulse_alpha)
            painter.setPen(QPen(pulse_color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center, pulse_radius, pulse_radius)
        
        # Draw main dot
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius - 1, radius - 1)
        
        # Inner highlight for running state
        if self._status == "running":
            highlight = QColor("#FFFFFF")
            highlight.setAlpha(60)
            painter.setBrush(QBrush(highlight))
            painter.drawEllipse(center.x() - 2, center.y() - 2, 4, 4)


class PathDisplay(QLabel):
    """Styled path display label with monospace font."""

    def __init__(self, placeholder: str = "No file or folder selected", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pathLabel")
        self.setText(placeholder)
        self.setWordWrap(True)
        self.setMinimumHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._placeholder = placeholder

    def set_path(self, path: str, selection_type: str = "Folder") -> None:
        """Set the displayed path and type."""
        if path:
            self.setText(f"{selection_type}: {path}")
        else:
            self.setText(self._placeholder)


class IPAddressDisplay(QLabel):
    """Styled IP address display with copy functionality."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ipLabel")
        self.setText("Detecting...")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to copy IP address")

    def set_ip(self, ip: str) -> None:
        """Set the IP address."""
        self.setText(ip if ip else "Not connected")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(self.text())
            self.setToolTip("Copied!")
            QToolTip.showText(event.globalPosition().toPoint(), "Copied!", self)


class URLDisplay(QLabel):
    """Styled shareable URL display with copy functionality."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("urlLabel")
        self.setText("Start the server to generate a shareable URL")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setWordWrap(True)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | 
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.setCursor(Qt.CursorShape.IBeamCursor)
        self._is_placeholder = True

    def set_url(self, url: str) -> None:
        """Set the shareable URL."""
        if url and not url.startswith("No active"):
            self._is_placeholder = False
            self.setObjectName("urlLabel")
            self.setText(url)
            self.setCursor(Qt.CursorShape.IBeamCursor)
        else:
            self._is_placeholder = True
            self.setObjectName("placeholderLabel")
            self.setText(url if url else "Start the server to generate a shareable URL")
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class PrimaryButton(QPushButton):
    """Primary action button (electric blue)."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("primaryButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(48)


class DangerButton(QPushButton):
    """Danger/stop button (red)."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("dangerButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(48)


class SecondaryButton(QPushButton):
    """Secondary button (gray)."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("secondaryButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)


class IconButton(QPushButton):
    """Icon-only button for toolbar actions."""

    def __init__(self, icon_char: str, tooltip: str = "", parent: QWidget | None = None) -> None:
        super().__init__(icon_char, parent)
        self.setObjectName("iconButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)
        self.setFixedSize(36, 36)


class PortSpinBox(QWidget):
    """Port input with validation (1-65535)."""

    valueChanged = Signal(int)

    def __init__(self, default_port: int = 8000, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.spinbox = QSpinBox()
        self.spinbox.setRange(1, 65535)
        self.spinbox.setValue(default_port)
        self.spinbox.setMinimumWidth(120)
        self.spinbox.setMaximumWidth(140)
        self.spinbox.setMinimumHeight(40)
        self.spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinbox.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.spinbox)

        self.label = QLabel("Port")
        self.label.setObjectName("sectionSubtitle")
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.label)
        layout.addStretch()

    def _on_value_changed(self, value: int) -> None:
        self.valueChanged.emit(value)

    def value(self) -> int:
        return self.spinbox.value()

    def setValue(self, value: int) -> None:
        self.spinbox.setValue(value)


class SelectionInfoWidget(QWidget):
    """Enhanced widget displaying detailed file/folder selection information."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._info: FileSelectionInfo | None = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)
        
        # Main path display with icon
        path_container = QWidget()
        path_container.setObjectName("pathContainer")
        path_layout = QHBoxLayout(path_container)
        path_layout.setContentsMargins(14, 12, 14, 12)
        path_layout.setSpacing(12)
        
        # File/folder icon
        self.icon_label = QLabel("📁")
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 20px;")
        path_layout.addWidget(self.icon_label)
        
        # Path text
        self.path_label = QLabel("No file or folder selected")
        self.path_label.setObjectName("pathLabel")
        self.path_label.setWordWrap(True)
        self.path_label.setMinimumHeight(20)
        self.path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        path_layout.addWidget(self.path_label, 1)
        
        layout.addWidget(path_container)
        
        # Details row (name, type, size)
        details_layout = QHBoxLayout()
        details_layout.setSpacing(16)
        
        self.name_label = QLabel("")
        self.name_label.setObjectName("sectionSubtitle")
        self.name_label.setStyleSheet("font-weight: 500;")
        details_layout.addWidget(self.name_label)
        
        self.type_label = QLabel("")
        self.type_label.setObjectName("sectionSubtitle")
        details_layout.addWidget(self.type_label)
        
        self.size_label = QLabel("")
        self.size_label.setObjectName("sectionSubtitle")
        details_layout.addWidget(self.size_label)
        
        details_layout.addStretch()
        layout.addLayout(details_layout)
        
        # Server root info (for files)
        self.server_root_label = QLabel("")
        self.server_root_label.setObjectName("placeholderLabel")
        self.server_root_label.setStyleSheet("font-style: italic; font-size: 11px;")
        self.server_root_label.setWordWrap(True)
        layout.addWidget(self.server_root_label)
        
        # Error message
        self.error_label = QLabel("")
        self.error_label.setObjectName("placeholderLabel")
        self.error_label.setStyleSheet("color: #FF5C68; font-size: 11px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Store original placeholder
        self._placeholder = "No file or folder selected"
    
    def set_info(self, info: FileSelectionInfo) -> None:
        """Set the selection info and update display."""
        self._info = info
        
        if info.selection_type == SelectionType.NONE or not info.path:
            self._show_placeholder()
            return
        
        # Set icon based on type
        if info.selection_type == SelectionType.FOLDER:
            self.icon_label.setText("📁")
        else:
            self.icon_label.setText("📄")
        
        # Show path with elision for long paths
        self.path_label.setText(info.path)
        self.path_label.setToolTip(info.path)
        
        # Show name
        self.name_label.setText(f"Name: {info.name}")
        
        # Show type
        type_text = info.selection_type.value
        if info.selection_type == SelectionType.FILE:
            type_text += " (serves parent folder)"
        self.type_label.setText(f"Type: {type_text}")
        
        # Show size for files
        if info.size_formatted:
            self.size_label.setText(f"Size: {info.size_formatted}")
        else:
            self.size_label.setText("")
        
        # Show server root info for files
        if info.selection_type == SelectionType.FILE:
            self.server_root_label.setText(
                f"ℹ HTTP server will serve the parent folder: {info.server_root}"
            )
            self.server_root_label.show()
        else:
            self.server_root_label.hide()
        
        # Show error if any
        if info.error_message:
            self.error_label.setText(f"⚠ {info.error_message}")
            self.error_label.show()
        else:
            self.error_label.hide()
    
    def _show_placeholder(self) -> None:
        """Show placeholder state."""
        self.icon_label.setText("📁")
        self.path_label.setText(self._placeholder)
        self.path_label.setToolTip("")
        self.name_label.setText("")
        self.type_label.setText("")
        self.size_label.setText("")
        self.server_root_label.hide()
        self.error_label.hide()
    
    def clear(self) -> None:
        """Clear the selection info."""
        self._info = None
        self._show_placeholder()
    
    def get_info(self) -> FileSelectionInfo | None:
        """Get the current selection info."""
        return self._info


class ElidedLabel(QLabel):
    """Label that elides text when too long, with tooltip showing full text."""
    
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._full_text = text
        self.setMouseTracking(True)
    
    def setText(self, text: str) -> None:
        self._full_text = text
        self._update_elided_text()
        self.setToolTip(text)
    
    def _update_elided_text(self) -> None:
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(
            self._full_text,
            Qt.TextElideMode.ElideMiddle,
            self.width() - 20
        )
        super().setText(elided)
    
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_elided_text()