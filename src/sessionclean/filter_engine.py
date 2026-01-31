"""Smart filtering to distinguish user-relevant files from system junk."""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path

from sessionclean.config import AppConfig
from sessionclean.constants import (
    IGNORED_DIRECTORIES,
    IGNORED_EXTENSIONS,
    IGNORED_PATH_FRAGMENTS,
)

logger = logging.getLogger("sessionclean")


class FilterEngine:
    """Determines whether a file is user-relevant or system junk.

    The filtering pipeline runs checks in order from cheapest to most expensive,
    short-circuiting on the first match (i.e., the first reason to exclude).
    """

    def __init__(self, config: AppConfig) -> None:
        # Merge defaults with user-configured exclusions
        self._ignored_extensions: set[str] = IGNORED_EXTENSIONS | {
            ext.lower() for ext in config.ignored_extensions
        }
        self._ignored_directories: set[str] = IGNORED_DIRECTORIES | {
            d.lower() for d in config.ignored_directories
        }
        self._ignored_path_fragments: set[str] = IGNORED_PATH_FRAGMENTS
        self._show_hidden: bool = config.show_hidden_files

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def should_include(self, file_path: str) -> bool:
        """Return True if the file is user-relevant and should be tracked.

        Returns False for system files, temp files, and other junk.
        """
        try:
            path_lower = file_path.lower()

            # Tier 1: Path fragment exclusion (fastest, pure string matching)
            if self._matches_ignored_path_fragment(path_lower):
                return False

            # Tier 2: Directory name exclusion
            if self._matches_ignored_directory(path_lower):
                return False

            # Tier 3: Extension exclusion
            if self._matches_ignored_extension(path_lower):
                return False

            # Tier 4: Hidden / system file attributes (requires stat call)
            if not self._show_hidden and self._is_hidden_or_system(file_path):
                return False

            # Tier 5: Zero-byte files
            if self._is_zero_byte(file_path):
                return False

            return True

        except (OSError, PermissionError) as exc:
            logger.debug("Filter check failed for %s: %s", file_path, exc)
            return False

    # ------------------------------------------------------------------
    # Filter tiers (private)
    # ------------------------------------------------------------------
    def _matches_ignored_path_fragment(self, path_lower: str) -> bool:
        """Check if the path contains any ignored fragment."""
        return any(frag in path_lower for frag in self._ignored_path_fragments)

    def _matches_ignored_directory(self, path_lower: str) -> bool:
        """Check if any directory component is in the ignored set."""
        parts = Path(path_lower).parts
        return any(part in self._ignored_directories for part in parts)

    def _matches_ignored_extension(self, path_lower: str) -> bool:
        """Check if the file extension is in the ignored set."""
        ext = Path(path_lower).suffix
        return ext in self._ignored_extensions

    def _is_hidden_or_system(self, file_path: str) -> bool:
        """Check Windows hidden or system file attributes."""
        try:
            attrs = os.stat(file_path).st_file_attributes  # type: ignore[attr-defined]
            hidden = bool(attrs & stat.FILE_ATTRIBUTE_HIDDEN)  # type: ignore[attr-defined]
            system = bool(attrs & stat.FILE_ATTRIBUTE_SYSTEM)  # type: ignore[attr-defined]
            return hidden or system
        except (AttributeError, OSError):
            # Not on Windows or stat failed
            return False

    def _is_zero_byte(self, file_path: str) -> bool:
        """Check if the file has zero bytes."""
        try:
            return os.path.getsize(file_path) == 0
        except OSError:
            return True  # If we can't check, skip it
