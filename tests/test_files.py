"""Unit tests for file selection service."""

import os
import tempfile
import stat
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

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


class TestFormatSize:
    """Tests for format_size function."""

    def test_bytes(self):
        assert format_size(500) == "500.0 B"

    def test_kilobytes(self):
        assert format_size(1024) == "1.0 KB"
        assert format_size(1536) == "1.5 KB"

    def test_megabytes(self):
        assert format_size(1024 * 1024) == "1.0 MB"
        assert format_size(1024 * 1024 * 1.5) == "1.5 MB"

    def test_gigabytes(self):
        assert format_size(1024 * 1024 * 1024) == "1.0 GB"

    def test_terabytes(self):
        assert format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"


class TestIsProtectedPath:
    """Tests for is_protected_path function."""

    @patch.dict(os.environ, {"SYSTEMROOT": "C:\\Windows", "PROGRAMFILES": "C:\\Program Files"})
    def test_windows_system_root(self):
        assert is_protected_path("C:\\Windows") is True
        assert is_protected_path("C:\\Windows\\System32") is True

    @patch.dict(os.environ, {"PROGRAMFILES": "C:\\Program Files"})
    def test_program_files(self):
        assert is_protected_path("C:\\Program Files") is True
        assert is_protected_path("C:\\Program Files\\App") is True

    @patch.dict(os.environ, {"PROGRAMFILES(X86)": "C:\\Program Files (x86)"})
    def test_program_files_x86(self):
        assert is_protected_path("C:\\Program Files (x86)") is True

    def test_drive_root(self):
        assert is_protected_path("C:\\") is True
        assert is_protected_path("D:\\") is True

    @patch("os.path.expanduser", return_value="C:\\Users\\TestUser")
    def test_user_home(self, mock_expanduser):
        assert is_protected_path("C:\\Users\\TestUser") is True

    def test_normal_path_not_protected(self):
        assert is_protected_path("C:\\Users\\TestUser\\Documents") is False
        assert is_protected_path("C:\\Projects\\MyApp") is False
        assert is_protected_path("D:\\Data\\Shared") is False


class TestValidatePath:
    """Tests for validate_path function."""

    def test_empty_path(self):
        valid, error = validate_path("", SelectionType.FOLDER)
        assert valid is False
        assert "No path provided" in error

    def test_nonexistent_path(self):
        valid, error = validate_path("C:\\Nonexistent\\Path", SelectionType.FOLDER)
        assert valid is False
        assert "does not exist" in error

    def test_folder_not_directory(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        
        valid, error = validate_path(str(file_path), SelectionType.FOLDER)
        assert valid is False
        assert "not a directory" in error

    def test_file_not_file(self, tmp_path):
        dir_path = tmp_path / "testdir"
        dir_path.mkdir()
        
        valid, error = validate_path(str(dir_path), SelectionType.FILE)
        assert valid is False
        assert "not a file" in error

    def test_valid_folder(self, tmp_path):
        valid, error = validate_path(str(tmp_path), SelectionType.FOLDER)
        assert valid is True
        assert error is None

    def test_valid_file(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        
        valid, error = validate_path(str(file_path), SelectionType.FILE)
        assert valid is True
        assert error is None


class TestGetFileSelectionInfo:
    """Tests for get_file_selection_info function."""

    def test_folder_selection(self, tmp_path):
        test_dir = tmp_path / "test_folder"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content")
        
        info = get_file_selection_info(str(test_dir), SelectionType.FOLDER)
        
        assert info.path == os.path.abspath(str(test_dir))
        assert info.selection_type == SelectionType.FOLDER
        assert info.name == "test_folder"
        assert info.parent_directory == os.path.abspath(str(tmp_path))
        assert info.size_bytes is None
        assert info.size_formatted is None
        assert info.is_readable is True
        assert info.error_message is None
        assert info.server_root == info.parent_directory

    def test_file_selection(self, tmp_path):
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("Hello World")
        
        info = get_file_selection_info(str(test_file), SelectionType.FILE)
        
        assert info.path == os.path.abspath(str(test_file))
        assert info.selection_type == SelectionType.FILE
        assert info.name == "test_file.txt"
        assert info.parent_directory == os.path.abspath(str(tmp_path))
        assert info.size_bytes == 11  # "Hello World"
        assert info.size_formatted == "11.0 B"
        assert info.is_readable is True
        assert info.error_message is None
        assert info.server_root == info.parent_directory

    def test_nonexistent_path_raises(self):
        with pytest.raises(FileSelectionError):
            get_file_selection_info("C:\\Nonexistent", SelectionType.FOLDER)

    def test_file_as_folder_raises(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        with pytest.raises(FileSelectionError):
            get_file_selection_info(str(test_file), SelectionType.FOLDER)

    def test_folder_as_file_raises(self, tmp_path):
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        
        with pytest.raises(FileSelectionError):
            get_file_selection_info(str(test_dir), SelectionType.FILE)


class TestCreateEmptySelection:
    """Tests for create_empty_selection function."""

    def test_empty_selection(self):
        info = create_empty_selection()
        
        assert info.path == ""
        assert info.selection_type == SelectionType.NONE
        assert info.name == ""
        assert info.parent_directory == ""
        assert info.size_bytes is None
        assert info.size_formatted is None
        assert info.is_readable is True
        assert info.error_message is None


class TestFileSelectionInfo:
    """Tests for FileSelectionInfo dataclass."""

    def test_server_root_property(self):
        info = FileSelectionInfo(
            path="C:\\Users\\Test\\file.txt",
            selection_type=SelectionType.FILE,
            name="file.txt",
            parent_directory="C:\\Users\\Test",
            size_bytes=100,
            size_formatted="100 B",
        )
        assert info.server_root == "C:\\Users\\Test"

    def test_str_representation(self):
        info = FileSelectionInfo(
            path="C:\\Users\\Test\\file.txt",
            selection_type=SelectionType.FILE,
            name="file.txt",
            parent_directory="C:\\Users\\Test",
        )
        assert "File" in str(info)
        assert "file.txt" in str(info)
        assert "C:\\Users\\Test\\file.txt" in str(info)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])