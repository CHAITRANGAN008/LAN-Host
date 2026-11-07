"""File selection and validation service for LAN Host."""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class SelectionType(Enum):
    """Type of file system selection."""
    FOLDER = "Folder"
    FILE = "File"
    NONE = "None"


class FileSelectionError(Exception):
    """Exception raised when file selection validation fails."""
    pass


@dataclass(frozen=True)
class FileSelectionInfo:
    """Information about a selected file or folder."""
    path: str
    selection_type: SelectionType
    name: str
    parent_directory: str
    size_bytes: int | None = None
    size_formatted: str | None = None
    is_readable: bool = True
    error_message: str | None = None

    @property
    def server_root(self) -> str:
        """Get the directory that will be served by HTTP server."""
        return self.parent_directory

    @property
    def display_path(self) -> str:
        """Get the path to display in UI."""
        return self.path

    def __str__(self) -> str:
        return f"{self.selection_type.value}: {self.name} ({self.path})"


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def is_protected_path(path: str) -> bool:
    """
    Check if path is a protected system path that should not be shared.
    
    Args:
        path: Absolute path to check.
        
    Returns:
        True if path is protected, False otherwise.
    """
    path = os.path.abspath(path).lower()
    
    # Windows protected paths
    protected = [
        os.environ.get("SYSTEMROOT", "C:\\Windows").lower(),
        os.environ.get("PROGRAMFILES", "C:\\Program Files").lower(),
        os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)").lower(),
        os.environ.get("APPDATA", "").lower(),
        os.environ.get("LOCALAPPDATA", "").lower(),
    ]
    
    # Paths that are explicitly allowed even if under protected paths
    # Get temp paths and normalize them (handle short names like CHAITR~1)
    temp_paths = set()
    for env_var in ["TEMP", "TMP"]:
        temp_val = os.environ.get(env_var, "")
        if temp_val:
            temp_paths.add(os.path.abspath(temp_val).lower())
    
    # Also add common temp directory names
    temp_paths.update(["temp", "tmp"])
    
    # Check if path is a drive root (e.g., C:\, D:\)
    drive_root = os.path.splitdrive(path)[0] + os.sep
    if path == drive_root.lower():
        return True
    
    # Check if path is user home directory
    user_home = os.path.expanduser("~").lower()
    if path == user_home:
        return True
    
    # Check if path is under an allowed subpath (like temp)
    for allowed in temp_paths:
        if allowed and (path == allowed or path.startswith(allowed + os.sep)):
            return False
    
    # Also check if path has "temp" as a path component (handles short vs long names)
    path_parts = path.split(os.sep)
    if "temp" in path_parts or "tmp" in path_parts:
        return False
    
    # Check protected paths
    for prot in protected:
        if prot and (path == prot or path.startswith(prot + os.sep)):
            return True
    
    return False


def validate_path(path: str, selection_type: SelectionType) -> tuple[bool, str | None]:
    """
    Validate a file or folder path.
    
    Args:
        path: Absolute path to validate.
        selection_type: Type of selection (FILE or FOLDER).
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    if not path:
        return False, "No path provided"
    
    # Check if path exists
    if not os.path.exists(path):
        return False, f"Path does not exist: {path}"
    
    # Check if it's the correct type
    if selection_type == SelectionType.FOLDER and not os.path.isdir(path):
        return False, f"Path is not a directory: {path}"
    
    if selection_type == SelectionType.FILE and not os.path.isfile(path):
        return False, f"Path is not a file: {path}"
    
    # Check readability
    if not os.access(path, os.R_OK):
        return False, f"Permission denied: cannot read {path}"
    
    # Check protected paths
    if is_protected_path(path):
        return False, f"Cannot share protected system path: {path}"
    
    # For folders, check if we can list contents
    if selection_type == SelectionType.FOLDER:
        try:
            os.listdir(path)
        except PermissionError:
            return False, f"Permission denied: cannot list directory {path}"
        except OSError as e:
            return False, f"Error accessing directory: {e}"
    
    return True, None


def get_file_selection_info(path: str, selection_type: SelectionType) -> FileSelectionInfo:
    """
    Get detailed information about a file or folder selection.
    
    Args:
        path: Absolute path to the file or folder.
        selection_type: Type of selection.
        
    Returns:
        FileSelectionInfo with details.
        
    Raises:
        FileSelectionError: If validation fails.
    """
    is_valid, error = validate_path(path, selection_type)
    if not is_valid:
        raise FileSelectionError(error)
    
    abs_path = os.path.abspath(path)
    name = os.path.basename(abs_path)
    parent_dir = os.path.dirname(abs_path)
    
    size_bytes = None
    size_formatted = None
    
    if selection_type == SelectionType.FILE:
        try:
            size_bytes = os.path.getsize(abs_path)
            size_formatted = format_size(size_bytes)
        except OSError:
            pass
    
    return FileSelectionInfo(
        path=abs_path,
        selection_type=selection_type,
        name=name,
        parent_directory=parent_dir,
        size_bytes=size_bytes,
        size_formatted=size_formatted,
        is_readable=True,
        error_message=None
    )


def create_empty_selection() -> FileSelectionInfo:
    """Create an empty selection info for cleared state."""
    return FileSelectionInfo(
        path="",
        selection_type=SelectionType.NONE,
        name="",
        parent_directory="",
        size_bytes=None,
        size_formatted=None,
        is_readable=True,
        error_message=None
    )