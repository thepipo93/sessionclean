"""File-related utility functions."""

from __future__ import annotations

from pathlib import Path


def format_size(size_bytes: int) -> str:
    """Format a byte count into a human-readable string.

    Examples:
        format_size(0)        -> "0 B"
        format_size(1023)     -> "1023 B"
        format_size(1024)     -> "1.0 KB"
        format_size(1048576)  -> "1.0 MB"
        format_size(5368709120) -> "5.0 GB"
    """
    if size_bytes < 0:
        return "0 B"

    units = [("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)]
    for unit, threshold in units:
        if size_bytes >= threshold:
            value = size_bytes / threshold
            return f"{value:.1f} {unit}"
    return f"{size_bytes} B"


def get_file_type(file_path: str) -> str:
    """Return a simple file type string based on extension.

    Examples:
        get_file_type("report.pdf") -> "pdf"
        get_file_type("image.PNG")  -> "png"
        get_file_type("noext")      -> ""
    """
    ext = Path(file_path).suffix.lower()
    return ext.lstrip(".") if ext else ""


# Category mapping for display grouping
FILE_CATEGORIES: dict[str, set[str]] = {
    "Documents": {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "rtf", "odt", "csv"},
    "Images": {"jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "ico", "tiff", "raw"},
    "Videos": {"mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v"},
    "Audio": {"mp3", "wav", "flac", "aac", "ogg", "wma", "m4a"},
    "Archives": {"zip", "rar", "7z", "tar", "gz", "bz2", "xz"},
    "Code": {"py", "js", "ts", "html", "css", "java", "cpp", "c", "h", "rs", "go", "rb"},
    "Installers": {"exe", "msi", "dmg", "deb", "rpm"},
}


def get_file_category(file_path: str) -> str:
    """Return the category of a file based on its extension.

    Returns "Other" if no category matches.
    """
    ext = get_file_type(file_path)
    if not ext:
        return "Other"
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"
