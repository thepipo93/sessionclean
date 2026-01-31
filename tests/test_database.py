"""Tests for the SQLite database module."""

import time
from pathlib import Path

import pytest

from sessionclean.database import SnapshotDatabase


@pytest.fixture
def db(tmp_dir: Path) -> SnapshotDatabase:
    """Provide a fresh database for each test."""
    database = SnapshotDatabase(db_path=tmp_dir / "test.db")
    database.initialize()
    return database


class TestSnapshotDatabase:
    def test_initialize_creates_tables(self, db: SnapshotDatabase):
        assert db.get_snapshot_count() == 0
        assert db.get_new_files_count() == 0

    def test_store_and_query_snapshot(self, db: SnapshotDatabase):
        records = [
            ("C:\\Users\\test\\file1.txt", 1000.0, 512),
            ("C:\\Users\\test\\file2.pdf", 2000.0, 1024),
            ("C:\\Users\\test\\file3.jpg", 3000.0, 2048),
        ]
        db.store_snapshot_batch(records)

        assert db.get_snapshot_count() == 3
        assert db.is_in_snapshot("C:\\Users\\test\\file1.txt") is True
        assert db.is_in_snapshot("C:\\Users\\test\\nonexistent.txt") is False

    def test_store_snapshot_ignores_duplicates(self, db: SnapshotDatabase):
        records = [("C:\\file.txt", 1000.0, 512)]
        db.store_snapshot_batch(records)
        db.store_snapshot_batch(records)  # Same record again

        assert db.get_snapshot_count() == 1

    def test_record_new_file(self, db: SnapshotDatabase):
        now = time.time()
        db.record_new_file("C:\\Users\\test\\download.zip", 5000, now, "zip")

        files = db.get_all_new_files()
        assert len(files) == 1
        assert files[0]["name"] == "download.zip"
        assert files[0]["size"] == 5000
        assert files[0]["file_type"] == "zip"

    def test_remove_new_file(self, db: SnapshotDatabase):
        now = time.time()
        db.record_new_file("C:\\Users\\test\\temp.txt", 100, now)

        assert db.get_new_files_count() == 1

        db.remove_new_file("C:\\Users\\test\\temp.txt")
        assert db.get_new_files_count() == 0

    def test_get_all_new_files_ordered_by_date(self, db: SnapshotDatabase):
        db.record_new_file("C:\\old.txt", 100, 1000.0)
        db.record_new_file("C:\\new.txt", 200, 2000.0)
        db.record_new_file("C:\\mid.txt", 150, 1500.0)

        files = db.get_all_new_files()
        assert files[0]["name"] == "new.txt"  # Most recent first
        assert files[1]["name"] == "mid.txt"
        assert files[2]["name"] == "old.txt"

    def test_new_file_includes_directory(self, db: SnapshotDatabase):
        db.record_new_file("C:\\Users\\test\\docs\\report.pdf", 1024, time.time())

        files = db.get_all_new_files()
        assert files[0]["directory"] == "C:\\Users\\test\\docs"

    def test_initialize_clears_previous_data(self, db: SnapshotDatabase):
        db.store_snapshot_batch([("C:\\file.txt", 1000.0, 512)])
        db.record_new_file("C:\\new.txt", 100, time.time())

        assert db.get_snapshot_count() == 1
        assert db.get_new_files_count() == 1

        db.initialize()  # Re-initialize should clear everything

        assert db.get_snapshot_count() == 0
        assert db.get_new_files_count() == 0

    def test_close(self, db: SnapshotDatabase):
        db.close()
        # After closing, a new connection should be created on next use
        assert db.get_snapshot_count() == 0
