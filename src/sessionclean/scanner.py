"""Startup snapshot scanner - records the initial file state."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from sessionclean.config import AppConfig
from sessionclean.constants import SCANNER_BATCH_SIZE
from sessionclean.database import SnapshotDatabase
from sessionclean.filter_engine import FilterEngine

logger = logging.getLogger("sessionclean")


class Scanner:
    """Walks monitored directories at startup and records the initial file set.

    The snapshot is used later to determine which files are "new" (created
    after the app started).
    """

    def __init__(
        self,
        config: AppConfig,
        db: SnapshotDatabase,
        filter_engine: FilterEngine,
    ) -> None:
        self._config = config
        self._db = db
        self._filter = filter_engine
        self._scan_start_time: float = 0.0
        self._is_scanning: bool = False
        self._total_files: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def scan_start_time(self) -> float:
        """Timestamp when the scan started."""
        return self._scan_start_time

    @property
    def is_scanning(self) -> bool:
        return self._is_scanning

    @property
    def total_files(self) -> int:
        return self._total_files

    def take_snapshot(self) -> int:
        """Scan all monitored paths and store the snapshot.

        Returns the total number of files recorded.
        Skips paths that are unavailable (e.g., disconnected drives).
        """
        self._scan_start_time = time.time()
        self._is_scanning = True
        self._total_files = 0

        active_paths = self._config.get_active_paths()
        logger.info(
            "Starting snapshot scan of %d paths: %s",
            len(active_paths),
            [mp.path for mp in active_paths],
        )

        for monitored_path in active_paths:
            try:
                count = self._scan_directory(
                    root=Path(monitored_path.path),
                    recursive=monitored_path.recursive,
                )
                self._total_files += count
                logger.info("Scanned %s: %d files", monitored_path.path, count)
            except (OSError, PermissionError) as exc:
                logger.warning("Failed to scan %s: %s", monitored_path.path, exc)

        self._is_scanning = False
        logger.info("Snapshot complete. Total files: %d", self._total_files)
        return self._total_files

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------
    def _scan_directory(self, root: Path, recursive: bool) -> int:
        """Walk a single directory tree, storing batches to the database.

        Uses os.scandir() for performance (faster than os.walk or Path.iterdir).
        """
        count = 0
        batch: list[tuple[str, float, int]] = []

        for file_path, mtime, size in self._iter_files(root, recursive):
            batch.append((file_path, mtime, size))
            count += 1

            if len(batch) >= SCANNER_BATCH_SIZE:
                self._db.store_snapshot_batch(batch)
                batch.clear()

        # Flush remaining
        if batch:
            self._db.store_snapshot_batch(batch)

        return count

    def _iter_files(self, root: Path, recursive: bool):
        """Yield (path, mtime, size) for all files under root."""
        try:
            with os.scandir(root) as entries:
                for entry in entries:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            stat_result = entry.stat(follow_symlinks=False)
                            yield (
                                entry.path,
                                stat_result.st_mtime,
                                stat_result.st_size,
                            )
                        elif recursive and entry.is_dir(follow_symlinks=False):
                            # Skip directories we know are junk
                            if entry.name.lower() not in self._filter._ignored_directories:
                                yield from self._iter_files(Path(entry.path), recursive)
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError) as exc:
            logger.debug("Cannot scan %s: %s", root, exc)
