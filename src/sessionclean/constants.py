"""Default constants, filter lists, and application paths."""

from pathlib import Path

# ---------------------------------------------------------------------------
# Application paths
# ---------------------------------------------------------------------------
APP_DIR = Path.home() / ".sessionclean"
CONFIG_PATH = APP_DIR / "config.json"
DB_PATH = APP_DIR / "session.db"
LOG_PATH = APP_DIR / "sessionclean.log"
INTERRUPTED_FLAG = APP_DIR / "interrupted.flag"

# ---------------------------------------------------------------------------
# Default monitored directories (populated on first run)
# ---------------------------------------------------------------------------
USER_HOME = Path.home()
DEFAULT_MONITORED_DIRS: list[str] = [
    str(USER_HOME / "Desktop"),
    str(USER_HOME / "Documents"),
    str(USER_HOME / "Downloads"),
    str(USER_HOME / "Pictures"),
    str(USER_HOME / "Videos"),
    str(USER_HOME / "Music"),
]

# ---------------------------------------------------------------------------
# File extensions to IGNORE (system / temp / build artifacts)
# ---------------------------------------------------------------------------
IGNORED_EXTENSIONS: set[str] = {
    # Temporary files
    ".tmp", ".temp", ".crdownload", ".partial", ".part", ".download",
    # Logs and traces
    ".log", ".etl",
    # System files
    ".dll", ".sys", ".dat", ".ini", ".drv",
    # Database locks
    ".lock", ".lck", ".db-journal", ".db-wal", ".db-shm",
    # Build artifacts
    ".pyc", ".pyo", ".o", ".obj", ".class",
    # Cache
    ".cache",
}

# ---------------------------------------------------------------------------
# Directory names to IGNORE (case-insensitive comparison)
# ---------------------------------------------------------------------------
IGNORED_DIRECTORIES: set[str] = {
    "appdata",
    ".cache",
    "__pycache__",
    "node_modules",
    ".git",
    ".hg",
    ".svn",
    "temp",
    "tmp",
    "$recycle.bin",
    "system volume information",
    ".vscode",
    ".idea",
    ".vs",
    ".gradle",
    "build",
    "dist",
    "venv",
    ".venv",
    "env",
    ".env",
}

# ---------------------------------------------------------------------------
# Path fragments to IGNORE (matched anywhere in the full path, lowercase)
# ---------------------------------------------------------------------------
IGNORED_PATH_FRAGMENTS: set[str] = {
    "\\appdata\\local\\temp",
    "\\appdata\\local\\microsoft",
    "\\appdata\\local\\google\\chrome\\user data",
    "\\appdata\\local\\packages",
    "\\appdata\\roaming\\microsoft",
    "\\programdata\\",
    "\\windows\\",
    "\\$recycle.bin\\",
    "\\system volume information\\",
}

# ---------------------------------------------------------------------------
# Scanner settings
# ---------------------------------------------------------------------------
SCANNER_BATCH_SIZE = 5000

# ---------------------------------------------------------------------------
# GUI settings
# ---------------------------------------------------------------------------
MAX_FILE_DISPLAY = 500
RECYCLE_BIN_RETENTION_DAYS = 30

# ---------------------------------------------------------------------------
# Shutdown hook
# ---------------------------------------------------------------------------
SHUTDOWN_BLOCK_REASON = "SessionClean is reviewing your new files..."
