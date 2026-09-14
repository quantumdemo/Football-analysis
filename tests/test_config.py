"""Tests for system configuration loading."""

import pytest
from src.config import SystemConfig
from src.errors import DataIntegrityError


def test_load_valid_config():
    config = SystemConfig.load_from_file("config/config.json")
    assert config.system_name == "FOOTBALL_AI_SYSTEM"
    assert config.freshness_threshold_hours == 72.0
    assert "odds" in config.prohibited_sources


def test_load_missing_config():
    with pytest.raises(DataIntegrityError):
        SystemConfig.load_from_file("config/non_existent.json")
