"""Unit tests for src.config.config_loader."""

import os
from pathlib import Path

import pytest

from src.config.config_loader import config


class TestResolveCredentialsPath:
    def test_relative_paths_are_anchored_to_the_repo_root(self):
        resolved = Path(config._resolve_credentials_path("config/key.json"))

        assert resolved.is_absolute()
        assert resolved == config._root / "config" / "key.json"

    def test_absolute_paths_are_left_untouched(self):
        absolute = Path(os.getcwd()).resolve() / "key.json"

        assert Path(config._resolve_credentials_path(str(absolute))) == absolute


class TestLookup:
    def test_reads_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("PAUHELPER_TEST_KEY", "value")

        assert config("PAUHELPER_TEST_KEY") == "value"

    def test_returns_the_default_for_unset_keys(self):
        assert config("PAUHELPER_MISSING_KEY", default="fallback") == "fallback"

    def test_unset_key_without_a_default_raises(self):
        with pytest.raises(RuntimeError, match="PAUHELPER_MISSING_KEY"):
            config("PAUHELPER_MISSING_KEY")
