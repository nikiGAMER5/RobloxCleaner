"""Utility helper functions for Roblox Cleaner."""

from __future__ import annotations

import os
from pathlib import Path


def format_bytes(size_bytes: int | float) -> str:
    """Format bytes into human-readable string (B, KB, MB, GB).

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted string like "1.25 GB" or "450 MB".
    """
    if size_bytes < 0:
        return "0 B"
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.2f} {units[unit_index]}"


def get_app_dir() -> Path:
    """Get the application data directory for Roblox Cleaner."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base_dir = Path(local_app_data)
    else:
        base_dir = Path.home() / "AppData" / "Local"
    
    app_dir = base_dir / "RobloxCleaner"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_local_appdata() -> Path:
    """Get the current user's LocalAppData path safely without hardcoding."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data)
    return Path.home() / "AppData" / "Local"


def get_temp_dir() -> Path:
    """Get the current user's Temp directory path safely."""
    temp_env = os.environ.get("TEMP") or os.environ.get("TMP")
    if temp_env:
        return Path(temp_env)
    return get_local_appdata() / "Temp"
