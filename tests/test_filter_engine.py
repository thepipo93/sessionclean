"""Tests for the smart file filtering engine."""

from pathlib import Path

import pytest

from sessionclean.config import AppConfig
from sessionclean.filter_engine import FilterEngine


@pytest.fixture
def engine() -> FilterEngine:
    """Provide a FilterEngine with default config."""
    return FilterEngine(AppConfig())


@pytest.fixture
def clean_engine() -> FilterEngine:
    """FilterEngine with path fragments cleared (for testing real temp files)."""
    eng = FilterEngine(AppConfig())
    eng._ignored_path_fragments = set()
    eng._ignored_directories = set()  # pytest tmp_path is inside AppData\Local\Temp
    return eng


@pytest.fixture
def populated_files(tmp_dir: Path) -> dict[str, Path]:
    """Create test files and return a dict of name -> path."""
    files = {}

    # User-relevant files
    f = tmp_dir / "report.pdf"
    f.write_bytes(b"pdf content")
    files["pdf"] = f

    f = tmp_dir / "photo.jpg"
    f.write_bytes(b"jpg content")
    files["jpg"] = f

    f = tmp_dir / "document.docx"
    f.write_bytes(b"docx content")
    files["docx"] = f

    # System junk
    f = tmp_dir / "debug.log"
    f.write_bytes(b"log data")
    files["log"] = f

    f = tmp_dir / "temp.tmp"
    f.write_bytes(b"temp data")
    files["tmp"] = f

    f = tmp_dir / "cache.cache"
    f.write_bytes(b"cache data")
    files["cache"] = f

    # Zero-byte file
    f = tmp_dir / "empty.txt"
    f.write_bytes(b"")
    files["empty"] = f

    return files


class TestFilterEngine:
    def test_includes_user_files(self, clean_engine: FilterEngine, populated_files):
        # Using clean_engine because tmp_dir is inside AppData\Local\Temp
        assert clean_engine.should_include(str(populated_files["pdf"])) is True
        assert clean_engine.should_include(str(populated_files["jpg"])) is True
        assert clean_engine.should_include(str(populated_files["docx"])) is True

    def test_excludes_ignored_extensions(self, clean_engine: FilterEngine, populated_files):
        assert clean_engine.should_include(str(populated_files["log"])) is False
        assert clean_engine.should_include(str(populated_files["tmp"])) is False
        assert clean_engine.should_include(str(populated_files["cache"])) is False

    def test_excludes_zero_byte_files(self, clean_engine: FilterEngine, populated_files):
        assert clean_engine.should_include(str(populated_files["empty"])) is False

    def test_excludes_appdata_paths(self, engine: FilterEngine):
        path = "C:\\Users\\test\\AppData\\Local\\Temp\\something.exe"
        assert engine.should_include(path) is False

    def test_excludes_programdata(self, engine: FilterEngine):
        path = "C:\\ProgramData\\SomeApp\\config.xml"
        assert engine.should_include(path) is False

    def test_excludes_windows_dir(self, engine: FilterEngine):
        path = "C:\\Windows\\System32\\drivers\\etc\\hosts"
        assert engine.should_include(path) is False

    def test_excludes_recycle_bin(self, engine: FilterEngine):
        path = "C:\\$Recycle.Bin\\S-1-5-21\\$RABCDEF.txt"
        assert engine.should_include(path) is False

    def test_excludes_node_modules(self, engine: FilterEngine, tmp_dir: Path):
        nm = tmp_dir / "node_modules" / "express" / "index.js"
        nm.parent.mkdir(parents=True)
        nm.write_bytes(b"module code")
        assert engine.should_include(str(nm)) is False

    def test_excludes_git_directory(self, engine: FilterEngine, tmp_dir: Path):
        git_file = tmp_dir / ".git" / "HEAD"
        git_file.parent.mkdir(parents=True)
        git_file.write_bytes(b"ref: refs/heads/main")
        assert engine.should_include(str(git_file)) is False

    def test_excludes_pycache(self, engine: FilterEngine, tmp_dir: Path):
        pyc = tmp_dir / "__pycache__" / "module.cpython-312.pyc"
        pyc.parent.mkdir(parents=True)
        pyc.write_bytes(b"bytecode")
        assert engine.should_include(str(pyc)) is False

    def test_custom_ignored_extensions(self, tmp_dir: Path):
        config = AppConfig(ignored_extensions=[".xyz", ".custom"])
        engine = FilterEngine(config)

        f = tmp_dir / "file.xyz"
        f.write_bytes(b"data")
        assert engine.should_include(str(f)) is False

    def test_custom_ignored_directories(self, tmp_dir: Path):
        config = AppConfig(ignored_directories=["my_junk_folder"])
        engine = FilterEngine(config)

        junk = tmp_dir / "my_junk_folder" / "file.pdf"
        junk.parent.mkdir(parents=True)
        junk.write_bytes(b"data")
        assert engine.should_include(str(junk)) is False

    def test_nonexistent_file_excluded(self, engine: FilterEngine):
        assert engine.should_include("C:\\nonexistent\\file.pdf") is False

    def test_crdownload_excluded(self, engine: FilterEngine, tmp_dir: Path):
        f = tmp_dir / "download.crdownload"
        f.write_bytes(b"partial download")
        assert engine.should_include(str(f)) is False
