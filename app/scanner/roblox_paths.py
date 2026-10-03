"""Definitions of Roblox directory targets, categories, and path resolvers."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Set

from app.utils.helpers import get_local_appdata, get_temp_dir


@dataclass
class RobloxCategory:
    """Represents a cleanable Roblox data category."""

    id: str
    name_de: str
    name_en: str
    description_de: str
    description_en: str
    icon_name: str
    resolve_targets: Callable[[], List[Path]]
    patterns: List[str] = field(default_factory=lambda: ["*"])
    recursive: bool = True


def get_allowed_roblox_roots() -> Set[Path]:
    """Get the set of permitted root directories for Roblox Cleaner operations.
    
    Any file to be cleaned MUST be a descendant of one of these roots.
    """
    local_app_data = get_local_appdata()
    temp_dir = get_temp_dir()

    roots = {
        local_app_data / "Roblox",
        local_app_data / "Bloxstrap",
        temp_dir / "Roblox",
        local_app_data / "CrashDumps",
        temp_dir,
    }

    return {r.resolve() for r in roots if r.exists()}


def _resolve_http_cache() -> List[Path]:
    """HTTP Meshes, Models, Textures and Sound Caches."""
    paths = []
    temp_roblox = get_temp_dir() / "Roblox"
    paths.append(temp_roblox / "http")
    paths.append(temp_roblox / "http-wob")
    
    local_roblox = get_local_appdata() / "Roblox"
    paths.append(local_roblox / "rbx-storage-sc")
    paths.append(local_roblox / "rbx-storage")
    return [p for p in paths if p.exists()]


def _resolve_logs() -> List[Path]:
    """Roblox client, studio and bootstrapper logs."""
    paths = []
    local_roblox = get_local_appdata() / "Roblox"
    paths.append(local_roblox / "logs")

    temp_roblox = get_temp_dir() / "Roblox"
    paths.append(temp_roblox / "raknet")

    bloxstrap_logs = get_local_appdata() / "Bloxstrap" / "Logs"
    if bloxstrap_logs.exists():
        paths.append(bloxstrap_logs)

    return [p for p in paths if p.exists()]


def _resolve_temp_files() -> List[Path]:
    """Temporary runtime data and cache folders."""
    paths = []
    temp_roblox = get_temp_dir() / "Roblox"
    paths.append(temp_roblox / "cache")
    paths.append(temp_roblox / "InternalPreloadSettings")

    local_roblox = get_local_appdata() / "Roblox"
    paths.append(local_roblox / "tmp-capture-storage")
    return [p for p in paths if p.exists()]


def _resolve_temp_root_files() -> List[Path]:
    """Explicit Roblox temp files directly in %TEMP% using fast os.scandir."""
    temp_dir = get_temp_dir()
    if not temp_dir.exists():
        return []

    matched = []
    try:
        with os.scandir(str(temp_dir)) as it:
            for entry in it:
                name_lower = entry.name.lower()
                if (
                    name_lower.startswith("rbx-")
                    or (name_lower.startswith("roblox") and (name_lower.endswith(".tmp") or name_lower.endswith(".log")))
                ):
                    matched.append(Path(entry.path))
    except Exception:
        pass
    return matched


def _resolve_media_cache() -> List[Path]:
    """Downloaded audio and video streaming cache."""
    paths = []
    temp_roblox = get_temp_dir() / "Roblox"
    paths.append(temp_roblox / "sounds")
    paths.append(temp_roblox / "videos")
    return [p for p in paths if p.exists()]


def _resolve_crash_dumps() -> List[Path]:
    """Windows and Roblox crash dump files."""
    dumps_dir = get_local_appdata() / "CrashDumps"
    if not dumps_dir.exists():
        return []

    matched = []
    try:
        with os.scandir(str(dumps_dir)) as it:
            for entry in it:
                if entry.name.lower().startswith("roblox") and entry.name.lower().endswith(".dmp"):
                    matched.append(Path(entry.path))
    except Exception:
        pass
    return matched


def _resolve_installer_temp() -> List[Path]:
    """Old installer downloads and OTA patch backups."""
    paths = []
    local_roblox = get_local_appdata() / "Roblox"
    paths.append(local_roblox / "Downloads")
    paths.append(local_roblox / "OTAPatchBackups")
    paths.append(local_roblox / "RobloxPlayerInstaller")
    paths.append(local_roblox / "RobloxStudioInstaller")
    paths.append(local_roblox / "Benchmark")
    return [p for p in paths if p.exists()]


def get_all_categories() -> List[RobloxCategory]:
    """Get list of all supported cleaning categories."""
    return [
        RobloxCategory(
            id="http_cache",
            name_de="HTTP & Asset Cache",
            name_en="HTTP & Asset Cache",
            description_de="Heruntergeladene Texturen, 3D-Modelle, Meshes und Sounds.",
            description_en="Downloaded textures, 3D models, meshes, and sound assets.",
            icon_name="cache",
            resolve_targets=_resolve_http_cache,
            patterns=["*"],
            recursive=True,
        ),
        RobloxCategory(
            id="logs",
            name_de="Roblox Logs & Diagnosen",
            name_en="Roblox Logs & Diagnostics",
            description_de="Player-, Studio- und Netzwerk-Verbindungs-Protokolle.",
            description_en="Player, Studio, and network connection diagnostic log files.",
            icon_name="logs",
            resolve_targets=_resolve_logs,
            patterns=["*.log", "*.txt", "*.dmp", "*"],
            recursive=True,
        ),
        RobloxCategory(
            id="temp_files",
            name_de="Temporäre Dateien",
            name_en="Temporary Files",
            description_de="Flüchtige Sitzungs- und Capture-Zwischendateien in AppData/Temp.",
            description_en="Volatile session and capture temporary files in AppData/Temp.",
            icon_name="temp",
            resolve_targets=lambda: _resolve_temp_files() + _resolve_temp_root_files(),
            patterns=["*"],
            recursive=True,
        ),
        RobloxCategory(
            id="media_cache",
            name_de="Medien-Cache",
            name_en="Media Cache",
            description_de="Gepufferte In-Game Soundeffekte und Videostreams.",
            description_en="Cached in-game sound effects and video streams.",
            icon_name="media",
            resolve_targets=_resolve_media_cache,
            patterns=["*"],
            recursive=True,
        ),
        RobloxCategory(
            id="crash_dumps",
            name_de="Absturzberichte (Crash Dumps)",
            name_en="Crash Dumps",
            description_de="Gespeicherte .dmp-Dateien früherer Roblox-Abstürze.",
            description_en="Saved .dmp crash dump files from Roblox application crashes.",
            icon_name="crash",
            resolve_targets=_resolve_crash_dumps,
            patterns=["*"],
            recursive=False,
        ),
        RobloxCategory(
            id="installer_temp",
            name_de="Installer & Patch Reste",
            name_en="Installer & Patch Leftovers",
            description_de="Alte Update-Pakete, OTA-Patch-Backups und Installer-Cache.",
            description_en="Old update packages, OTA patch backups, and installer cache.",
            icon_name="installer",
            resolve_targets=_resolve_installer_temp,
            patterns=["*"],
            recursive=True,
        ),
    ]
