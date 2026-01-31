"""Shared pytest fixtures for SessionClean tests."""

import tempfile
from pathlib import Path

import pytest

from sessionclean.config import AppConfig, MonitoredPath


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """Provide a clean temporary directory for each test."""
    return tmp_path


@pytest.fixture
def sample_config(tmp_dir: Path) -> AppConfig:
    """Return a config pointing to the temporary directory."""
    return AppConfig(
        monitored_paths=[
            MonitoredPath(path=str(tmp_dir), recursive=True, enabled=True, is_removable=False),
        ],
    )


@pytest.fixture
def populated_dir(tmp_dir: Path) -> Path:
    """Create a temp directory with sample files for testing."""
    # User-like files
    (tmp_dir / "report.pdf").write_bytes(b"fake pdf content here")
    (tmp_dir / "photo.jpg").write_bytes(b"fake jpg data " * 100)
    (tmp_dir / "notes.txt").write_text("some notes", encoding="utf-8")

    # Nested directory
    sub = tmp_dir / "projects" / "my_app"
    sub.mkdir(parents=True)
    (sub / "main.py").write_text("print('hello')", encoding="utf-8")

    # System-like junk
    (tmp_dir / "debug.log").write_bytes(b"log data")
    (tmp_dir / "temp_file.tmp").write_bytes(b"temp")
    (tmp_dir / "thumbs.db").write_bytes(b"thumbs")

    return tmp_dir
