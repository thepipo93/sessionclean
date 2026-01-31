"""SQLite-based storage for startup snapshots and session file tracking."""

from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path

from sessionclean.constants import APP_DIR, DB_PATH

logger = logging.getLogger("sessionclean")


class SnapshotDatabase:
    """Stores the startup file snapshot and tracks new files during the session.

    Thread-safe: each thread gets its own connection via thread-local storage.
    """

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._db_path = db_path
        self._local = threading.local()
        self._lock = threading.Lock()
        APP_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------
    def _get_conn(self) -> sqlite3.Connection:
        """Get or create a thread-local database connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(str(self._db_path), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    # ------------------------------------------------------------------
    # Schema initialization
    # ------------------------------------------------------------------
    def initialize(self) -> None:
        """Create tables and clear previous session data."""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS snapshot (
                path    TEXT PRIMARY KEY,
                mtime   REAL NOT NULL,
                size    INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS new_files (
                path        TEXT PRIMARY KEY,
                size        INTEGER NOT NULL,
                created_at  REAL NOT NULL,
                file_type   TEXT NOT NULL DEFAULT ''
            );

            DELETE FROM snapshot;
            DELETE FROM new_files;
        """)
        conn.commit()
        logger.info("Database initialized at %s", self._db_path)

    # ------------------------------------------------------------------
    # Snapshot operations
    # ------------------------------------------------------------------
    def store_snapshot_batch(self, file_records: list[tuple[str, float, int]]) -> None:
        """Bulk insert snapshot records: [(path, mtime, size), ...].

        Uses INSERT OR IGNORE to skip duplicates.
        """
        conn = self._get_conn()
        with self._lock:
            conn.executemany(
                "INSERT OR IGNORE INTO snapshot (path, mtime, size) VALUES (?, ?, ?)",
                file_records,
            )
            conn.commit()

    def is_in_snapshot(self, path: str) -> bool:
        """Check if a file existed at startup."""
        conn = self._get_conn()
        row = conn.execute("SELECT 1 FROM snapshot WHERE path = ?", (path,)).fetchone()
        return row is not None

    def get_snapshot_count(self) -> int:
        """Return the total number of files in the snapshot."""
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) FROM snapshot").fetchone()
        return row[0] if row else 0

    # ------------------------------------------------------------------
    # New files tracking
    # ------------------------------------------------------------------
    def record_new_file(self, path: str, size: int, created_at: float, file_type: str = "") -> None:
        """Record a file created/downloaded during the session."""
        conn = self._get_conn()
        with self._lock:
            conn.execute(
                """INSERT OR REPLACE INTO new_files (path, size, created_at, file_type)
                   VALUES (?, ?, ?, ?)""",
                (path, size, created_at, file_type),
            )
            conn.commit()
        logger.debug("Recorded new file: %s (%d bytes)", path, size)

    def remove_new_file(self, path: str) -> None:
        """Remove from new_files if a tracked file was deleted during the session."""
        conn = self._get_conn()
        with self._lock:
            conn.execute("DELETE FROM new_files WHERE path = ?", (path,))
            conn.commit()
        logger.debug("Removed tracked file: %s", path)

    def get_all_new_files(self) -> list[dict]:
        """Return all files created during this session as a list of dicts."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT path, size, created_at, file_type
               FROM new_files
               ORDER BY created_at DESC"""
        ).fetchall()
        return [
            {
                "path": row["path"],
                "name": Path(row["path"]).name,
                "size": row["size"],
                "created_at": row["created_at"],
                "file_type": row["file_type"],
                "directory": str(Path(row["path"]).parent),
            }
            for row in rows
        ]

    def get_new_files_count(self) -> int:
        """Return the number of new files tracked this session."""
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) FROM new_files").fetchone()
        return row[0] if row else 0

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close the thread-local connection if open."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
