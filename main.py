#!/usr/bin/env python3
"""
LAN Host - Main Entry Point

A portable Windows desktop application that allows users to host local files
and folders over their Wi-Fi/LAN network using Python's HTTP server.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui.main_window import MainWindow  # type: ignore


def main() -> int:
    """Application entry point."""
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setApplicationName("LAN Host")
    app.setApplicationVersion("0.1.0")
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())