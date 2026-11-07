# LAN Host - Portable LAN File Sharing Application

A portable Windows desktop application that allows users to host local files and folders 
over their Wi-Fi/LAN network using Python's built-in HTTP server.

## Features
- Host any local directory over LAN/Wi-Fi
- Simple PySide6 GUI for configuration
- Automatic local IP detection
- QR code generation for easy mobile access
- Portable - no installation required (when built with PyInstaller)

## Requirements
- Python 3.8+
- PySide6
- psutil

## Installation

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Project Structure

```
LAN-Host/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── .gitignore           # Git ignore rules
├── src/
│   ├── __init__.py      # Package init
│   ├── ui/              # PySide6 UI components
│   │   └── __init__.py
│   ├── core/            # Core application logic
│   │   └── __init__.py
│   ├── services/        # Background services (HTTP server, etc.)
│   │   └── __init__.py
│   └── utils/           # Utility functions
│       └── __init__.py
├── assets/
│   └── icons/           # Application icons and images
└── tests/               # Unit and integration tests
```

## Architecture

- **src/ui/** - All PySide6 widgets, windows, and UI logic
- **src/core/** - Business logic, configuration, and application state
- **src/services/** - Long-running background services (HTTP server, network discovery)
- **src/utils/** - Shared utility functions (network helpers, file operations)

## Building Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=assets/icons/app.ico main.py
```

## License

MIT License