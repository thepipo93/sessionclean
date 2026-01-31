"""Utilities for detecting and checking external/removable drives."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("sessionclean")


def is_drive_available(path: str) -> bool:
    """Check if a drive or path is currently accessible."""
    try:
        return Path(path).exists()
    except (OSError, PermissionError):
        return False


def get_drive_letter(path: str) -> str | None:
    """Extract the drive letter from a Windows path (e.g., 'C' from 'C:\\Users')."""
    resolved = str(Path(path).resolve())
    if len(resolved) >= 2 and resolved[1] == ":":
        return resolved[0].upper()
    return None


def is_removable_drive(path: str) -> bool:
    """Heuristic check: a drive is likely removable if it's not C:\\.

    For a more accurate check, we could use ctypes + GetDriveTypeW,
    but this simple heuristic works for the MVP.
    """
    letter = get_drive_letter(path)
    if letter is None:
        return False
    return letter not in ("C",)


def get_available_drives() -> list[str]:
    """Return a list of currently available drive letters on Windows."""
    drives = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            drives.append(letter)
    return drives
