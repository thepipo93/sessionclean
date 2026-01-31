"""Configuration loading, saving, and defaults for SessionClean."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from sessionclean.constants import (
    APP_DIR,
    CONFIG_PATH,
    DEFAULT_MONITORED_DIRS,
    MAX_FILE_DISPLAY,
    RECYCLE_BIN_RETENTION_DAYS,
)

logger = logging.getLogger("sessionclean")


@dataclass
class MonitoredPath:
    """A single path to monitor for new files."""

    path: str
    recursive: bool = True
    enabled: bool = True
    is_removable: bool = False  # True for external / USB drives

    def exists(self) -> bool:
        """Check if the path is currently accessible."""
        return Path(self.path).exists()


@dataclass
class AppConfig:
    """Application-wide configuration."""

    monitored_paths: list[MonitoredPath] = field(default_factory=list)
    ignored_extensions: list[str] = field(default_factory=list)
    ignored_directories: list[str] = field(default_factory=list)
    show_hidden_files: bool = False
    max_file_display: int = MAX_FILE_DISPLAY
    recycle_bin_days: int = RECYCLE_BIN_RETENTION_DAYS
    theme: str = "dark"

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    @classmethod
    def load(cls) -> AppConfig:
        """Load config from disk, or create defaults if missing."""
        if not CONFIG_PATH.exists():
            logger.info("No config file found. Creating defaults.")
            config = cls.get_defaults()
            config.save()
            return config

        try:
            raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            monitored = [MonitoredPath(**mp) for mp in raw.get("monitored_paths", [])]
            return cls(
                monitored_paths=monitored,
                ignored_extensions=raw.get("ignored_extensions", []),
                ignored_directories=raw.get("ignored_directories", []),
                show_hidden_files=raw.get("show_hidden_files", False),
                max_file_display=raw.get("max_file_display", MAX_FILE_DISPLAY),
                recycle_bin_days=raw.get("recycle_bin_days", RECYCLE_BIN_RETENTION_DAYS),
                theme=raw.get("theme", "dark"),
            )
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.error("Failed to parse config: %s. Using defaults.", exc)
            config = cls.get_defaults()
            config.save()
            return config

    def save(self) -> None:
        """Persist current config to disk."""
        APP_DIR.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        CONFIG_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Config saved to %s", CONFIG_PATH)

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------
    @classmethod
    def get_defaults(cls) -> AppConfig:
        """Return a config pre-populated with standard user directories."""
        monitored = []
        for dir_path in DEFAULT_MONITORED_DIRS:
            if Path(dir_path).exists():
                monitored.append(
                    MonitoredPath(path=dir_path, recursive=True, enabled=True, is_removable=False)
                )
        return cls(monitored_paths=monitored)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def add_path(self, path: str, recursive: bool = True, is_removable: bool = False) -> None:
        """Add a new monitored path if it doesn't already exist."""
        normalized = str(Path(path).resolve())
        for mp in self.monitored_paths:
            if str(Path(mp.path).resolve()) == normalized:
                logger.warning("Path already monitored: %s", path)
                return
        self.monitored_paths.append(
            MonitoredPath(
                path=normalized, recursive=recursive,
                enabled=True, is_removable=is_removable,
            )
        )
        logger.info("Added monitored path: %s", normalized)

    def remove_path(self, path: str) -> None:
        """Remove a monitored path."""
        normalized = str(Path(path).resolve())
        self.monitored_paths = [
            mp for mp in self.monitored_paths
            if str(Path(mp.path).resolve()) != normalized
        ]

    def get_active_paths(self) -> list[MonitoredPath]:
        """Return only enabled paths that currently exist on disk."""
        return [mp for mp in self.monitored_paths if mp.enabled and mp.exists()]
