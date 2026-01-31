"""Tests for the configuration module."""

import json
from pathlib import Path

import pytest

from sessionclean.config import AppConfig, MonitoredPath


class TestMonitoredPath:
    def test_exists_true(self, tmp_dir: Path):
        mp = MonitoredPath(path=str(tmp_dir))
        assert mp.exists() is True

    def test_exists_false(self):
        mp = MonitoredPath(path=r"Z:\nonexistent\path")
        assert mp.exists() is False

    def test_defaults(self):
        mp = MonitoredPath(path="C:\\test")
        assert mp.recursive is True
        assert mp.enabled is True
        assert mp.is_removable is False


class TestAppConfig:
    def test_get_defaults(self):
        config = AppConfig.get_defaults()
        assert isinstance(config.monitored_paths, list)
        assert config.theme == "dark"
        assert config.show_hidden_files is False
        assert config.recycle_bin_days == 30

    def test_save_and_load(self, tmp_dir: Path, monkeypatch):
        config_path = tmp_dir / "config.json"
        app_dir = tmp_dir

        monkeypatch.setattr("sessionclean.config.CONFIG_PATH", config_path)
        monkeypatch.setattr("sessionclean.config.APP_DIR", app_dir)

        original = AppConfig(
            monitored_paths=[
                MonitoredPath(path=str(tmp_dir), recursive=False, is_removable=True),
            ],
            theme="light",
            max_file_display=200,
        )
        original.save()

        assert config_path.exists()

        loaded = AppConfig.load()
        assert len(loaded.monitored_paths) == 1
        assert loaded.monitored_paths[0].path == str(tmp_dir)
        assert loaded.monitored_paths[0].recursive is False
        assert loaded.monitored_paths[0].is_removable is True
        assert loaded.theme == "light"
        assert loaded.max_file_display == 200

    def test_load_corrupted_file(self, tmp_dir: Path, monkeypatch):
        config_path = tmp_dir / "config.json"
        app_dir = tmp_dir
        config_path.write_text("{invalid json", encoding="utf-8")

        monkeypatch.setattr("sessionclean.config.CONFIG_PATH", config_path)
        monkeypatch.setattr("sessionclean.config.APP_DIR", app_dir)

        config = AppConfig.load()
        # Should fall back to defaults
        assert isinstance(config, AppConfig)
        assert config.theme == "dark"

    def test_add_path(self, tmp_dir: Path):
        config = AppConfig()
        config.add_path(str(tmp_dir))
        assert len(config.monitored_paths) == 1

        # Adding the same path again should not duplicate
        config.add_path(str(tmp_dir))
        assert len(config.monitored_paths) == 1

    def test_remove_path(self, tmp_dir: Path):
        config = AppConfig()
        config.add_path(str(tmp_dir))
        assert len(config.monitored_paths) == 1

        config.remove_path(str(tmp_dir))
        assert len(config.monitored_paths) == 0

    def test_get_active_paths(self, tmp_dir: Path):
        config = AppConfig(
            monitored_paths=[
                MonitoredPath(path=str(tmp_dir), enabled=True),
                MonitoredPath(path=r"Z:\nonexistent", enabled=True),
                MonitoredPath(path=str(tmp_dir), enabled=False),
            ]
        )
        active = config.get_active_paths()
        assert len(active) == 1
        assert active[0].path == str(tmp_dir)
