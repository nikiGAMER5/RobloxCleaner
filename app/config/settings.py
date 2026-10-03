"""Configuration and settings manager for Roblox Cleaner."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict

from app.utils.helpers import get_app_dir


@dataclass
class AppSettings:
    """Dataclass holding all user configurable options."""

    backup_enabled: bool = False
    backup_dir: str = ""
    confirm_before_clean: bool = True
    theme: str = "dark"
    language: str = "en"
    warn_roblox_running: bool = True
    enabled_categories: Dict[str, bool] = field(
        default_factory=lambda: {
            "http_cache": True,
            "logs": True,
            "temp_files": True,
            "media_cache": True,
            "crash_dumps": True,
            "installer_temp": True,
        }
    )

    def __post_init__(self) -> None:
        if not self.backup_dir:
            self.backup_dir = str(get_app_dir() / "Backups")


class SettingsManager:
    """Loads and saves application settings safely."""

    def __init__(self, config_file: Path | None = None) -> None:
        self.config_file = config_file or (get_app_dir() / "settings.json")
        self.settings: AppSettings = self.load()

    def load(self) -> AppSettings:
        """Load settings from JSON file or return defaults if missing/corrupt."""
        if not self.config_file.exists():
            return AppSettings()

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            valid_keys = set(AppSettings.__dataclass_fields__.keys())
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            return AppSettings(**filtered)
        except Exception:
            return AppSettings()

    def save(self, settings: AppSettings | None = None) -> bool:
        """Save settings to JSON file."""
        if settings is not None:
            self.settings = settings

        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.settings), f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def get(self) -> AppSettings:
        """Get current settings."""
        return self.settings

    def update(self, **kwargs: Any) -> None:
        """Update individual setting keys and persist."""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.save()
