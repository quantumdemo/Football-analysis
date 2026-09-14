"""Configuration management module."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from src.errors import DataIntegrityError


@dataclass
class SystemConfig:
    """Holds system settings loaded from configuration."""
    system_name: str
    version: str
    freshness_threshold_hours: float
    min_reliability_score: float
    prohibited_sources: List[str]

    @classmethod
    def load_from_file(cls, filepath: str = "config/config.json") -> "SystemConfig":
        path = Path(filepath)
        if not path.exists():
            raise DataIntegrityError(f"Configuration file not found at {filepath}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise DataIntegrityError(f"Failed to parse configuration file: {e}")

        required_keys = [
            "system_name", "version", "freshness_threshold_hours",
            "min_reliability_score", "prohibited_sources"
        ]
        for key in required_keys:
            if key not in data:
                raise DataIntegrityError(f"Missing required configuration key: {key}")

        return cls(
            system_name=data["system_name"],
            version=data["version"],
            freshness_threshold_hours=float(data["freshness_threshold_hours"]),
            min_reliability_score=float(data["min_reliability_score"]),
            prohibited_sources=list(data["prohibited_sources"])
        )
