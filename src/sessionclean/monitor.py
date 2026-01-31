"""Real-time file system monitoring using watchdog."""

from __future__ import annotations

import logging
import os
import time

from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileMovedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from sessionclean.config import AppConfig, MonitoredPath
from sessionclean.database import SnapshotDatabase
from sessionclean.filter_engine import FilterEngine
from sessionclean.utils.file_utils import get_file_type

logger = logging.getLogger("sessionclean")


class SessionFileHandler(FileSystemEventHandler):
    """Handles file creation, move, and deletion events.

    Only tracks files that pass the filter engine and didn't exist
    in the startup snapshot.
    """

    def __init__(
        self,
        db: SnapshotDatabase,
        filter_engine: FilterEngine,
        scan_start_time: float,
    ) -> None:
        super().__init__()
        self._db = db
        self._filter = filter_engine
        self._scan_start_time = scan_start_time

    def on_created(self, event: FileCreatedEvent) -> None:
        """Record a newly created file if it passes filters."""
        if event.is_directory:
            return
        self._try_record(event.src_path)

    def on_moved(self, event: FileMovedEvent) -> None:
        """Track file if moved into a monitored directory."""
        if event.is_directory:
            return
        # Remove old path if tracked
        self._db.remove_new_file(event.src_path)
        # Record new path
        self._try_record(event.dest_path)

    def on_deleted(self, event: FileDeletedEvent) -> None:
        """Remove from new_files if a tracked file is deleted during the session."""
        if event.is_directory:
            return
        self._db.remove_new_file(event.src_path)

    def _try_record(self, file_path: str) -> None:
        """Check filters and snapshot, then record if appropriate."""
        if not self._filter.should_include(file_path):
            return

        # Don't record files that existed at startup
        if self._db.is_in_snapshot(file_path):
            return

        try:
            size = os.path.getsize(file_path)
            file_type = get_file_type(file_path)
            self._db.record_new_file(
                path=file_path,
                size=size,
                created_at=time.time(),
                file_type=file_type,
            )
        except (OSError, PermissionError) as exc:
            logger.debug("Could not record %s: %s", file_path, exc)


class FileMonitor:
    """Manages watchdog Observer instances for all monitored paths."""

    def __init__(
        self,
        config: AppConfig,
        db: SnapshotDatabase,
        filter_engine: FilterEngine,
        scan_start_time: float = 0.0,
    ) -> None:
        self._config = config
        self._db = db
        self._filter = filter_engine
        self._scan_start_time = scan_start_time
        self._observers: dict[str, Observer] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start an Observer for each enabled and available monitored path."""
        active_paths = self._config.get_active_paths()
        logger.info("Starting file monitor for %d paths", len(active_paths))

        for mp in active_paths:
            self._start_observer(mp)

    def stop(self) -> None:
        """Stop all observers gracefully."""
        logger.info("Stopping all file monitors")
        for path, observer in self._observers.items():
            try:
                observer.stop()
                observer.join(timeout=5)
                logger.debug("Stopped observer for %s", path)
            except Exception as exc:
                logger.warning("Error stopping observer for %s: %s", path, exc)
        self._observers.clear()

    # ------------------------------------------------------------------
    # Individual observer management
    # ------------------------------------------------------------------
    def _start_observer(self, mp: MonitoredPath) -> None:
        """Start a single observer for a monitored path."""
        if mp.path in self._observers:
            logger.debug("Observer already running for %s", mp.path)
            return

        try:
            handler = SessionFileHandler(
                db=self._db,
                filter_engine=self._filter,
                scan_start_time=self._scan_start_time,
            )
            observer = Observer()
            observer.schedule(handler, mp.path, recursive=mp.recursive)
            observer.daemon = True
            observer.start()
            self._observers[mp.path] = observer
            logger.info("Started monitoring: %s (recursive=%s)", mp.path, mp.recursive)
        except (OSError, PermissionError) as exc:
            logger.warning("Cannot monitor %s: %s", mp.path, exc)

    def restart_observer(self, path: str) -> None:
        """Restart a single observer (e.g., when a drive reconnects)."""
        if path in self._observers:
            try:
                self._observers[path].stop()
                self._observers[path].join(timeout=5)
            except Exception:
                pass
            del self._observers[path]

        for mp in self._config.get_active_paths():
            if mp.path == path:
                self._start_observer(mp)
                break

    @property
    def active_paths(self) -> list[str]:
        """Return the list of currently monitored paths."""
        return list(self._observers.keys())
