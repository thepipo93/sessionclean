"""Tests for the startup snapshot scanner."""

import time
from pathlib import Path

import pytest

from sessionclean.config import AppConfig, MonitoredPath
from sessionclean.database import SnapshotDatabase
from sessionclean.filter_engine import FilterEngine
from sessionclean.scanner import Scanner


@pytest.fixture
def db(tmp_dir: Path) -> SnapshotDatabase:
    database = SnapshotDatabase(db_path=tmp_dir / "test.db")
    database.initialize()
    return database


@pytest.fixture
def engine() -> FilterEngine:
    return FilterEngine(AppConfig())


class TestScanner:
    def test_scan_empty_directory(self, tmp_dir: Path, db, engine):
        # Use a clean subdirectory to avoid pytest artifacts in tmp_dir
        empty_dir = tmp_dir / "truly_empty"
        empty_dir.mkdir()
        config = AppConfig(
            monitored_paths=[MonitoredPath(path=str(empty_dir))]
        )
        scanner = Scanner(config, db, engine)
        count = scanner.take_snapshot()
        assert count == 0

    def test_scan_with_files(self, populated_dir: Path, db, engine):
        config = AppConfig(
            monitored_paths=[MonitoredPath(path=str(populated_dir))]
        )
        scanner = Scanner(config, db, engine)
        count = scanner.take_snapshot()

        # populated_dir has: report.pdf, photo.jpg, notes.txt, main.py
        # Excluded by filter: debug.log, temp_file.tmp, thumbs.db
        assert count >= 4  # At least the user files
        assert scanner.is_scanning is False
        assert scanner.scan_start_time > 0

    def test_scan_records_in_database(self, populated_dir: Path, db, engine):
        config = AppConfig(
            monitored_paths=[MonitoredPath(path=str(populated_dir))]
        )
        scanner = Scanner(config, db, engine)
        scanner.take_snapshot()

        # The pdf should be in the snapshot
        pdf_path = str(populated_dir / "report.pdf")
        assert db.is_in_snapshot(pdf_path) is True

    def test_scan_skips_unavailable_path(self, tmp_dir: Path, db, engine):
        config = AppConfig(
            monitored_paths=[
                MonitoredPath(path=str(tmp_dir)),
                MonitoredPath(path=r"Z:\nonexistent\drive"),
            ]
        )
        scanner = Scanner(config, db, engine)
        # Should not raise, just skip the unavailable path
        count = scanner.take_snapshot()
        assert count >= 0

    def test_scan_non_recursive(self, tmp_dir: Path, db, engine):
        # Create files in root and subdirectory
        (tmp_dir / "root_file.txt").write_text("root", encoding="utf-8")
        sub = tmp_dir / "subdir"
        sub.mkdir()
        (sub / "nested_file.txt").write_text("nested", encoding="utf-8")

        config = AppConfig(
            monitored_paths=[MonitoredPath(path=str(tmp_dir), recursive=False)]
        )
        scanner = Scanner(config, db, engine)
        count = scanner.take_snapshot()

        assert db.is_in_snapshot(str(tmp_dir / "root_file.txt")) is True
        assert db.is_in_snapshot(str(sub / "nested_file.txt")) is False

    def test_scan_skips_ignored_directories(self, tmp_dir: Path, db, engine):
        # Create a file inside node_modules
        nm = tmp_dir / "node_modules" / "express"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("module", encoding="utf-8")

        # Create a normal file
        (tmp_dir / "app.js").write_text("app", encoding="utf-8")

        config = AppConfig(
            monitored_paths=[MonitoredPath(path=str(tmp_dir))]
        )
        scanner = Scanner(config, db, engine)
        scanner.take_snapshot()

        assert db.is_in_snapshot(str(tmp_dir / "app.js")) is True
        assert db.is_in_snapshot(str(nm / "index.js")) is False
