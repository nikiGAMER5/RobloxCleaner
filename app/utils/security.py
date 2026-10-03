"""Security mechanisms and path validation for Roblox Cleaner."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

BLOCKED_SYSTEM_DIR_NAMES = {
    "windows",
    "system32",
    "syswow64",
    "winsxs",
    "boot",
    "recovery",
    "program files",
    "program files (x86)",
    "system volume information",
    "$recycle.bin",
    "perflogs",
}

BLOCKED_ROBLOX_FILENAMES = {
    "globalbasicsettings_13.xml",
    "globalbasicsettings_13_studio.xml",
    "analysticssettings.xml",
    "frm.cfg",
    "clientappsettings.json",
}

BLOCKED_ROBLOX_DIR_NAMES = {
    "versions",
    "clientsettings",
    "localstorage",
    "universalapp",
    "otaplugins",
    "defaultinstances",
    "builtinflugins",
}

BLOCKED_SENSITIVE_KEYWORDS = {
    "cookie",
    "token",
    "auth",
    "secret",
    "credential",
    "password",
    ".roblosecurity",
}


class SecurityValidator:
    """Validates paths and operations to ensure complete safety before scanning or deleting."""

    @classmethod
    def is_safe_roblox_target(cls, target_path: Path, allowed_roots: Iterable[Path]) -> tuple[bool, str]:
        """Verify whether a target path is strictly within the allowed Roblox roots.

        Args:
            target_path: Path to validate.
            allowed_roots: Predefined safe Roblox parent directories.

        Returns:
            (is_safe, reason)
        """
        try:
            resolved_target = target_path.resolve()
        except Exception as exc:
            return False, f"Ungültiger Pfad ({exc})"

        if len(resolved_target.parts) <= 2:
            return False, "Kritisches Root- oder Laufwerksverzeichnis blockiert."

        target_parts_lower = [p.lower() for p in resolved_target.parts]
        for blocked in BLOCKED_SYSTEM_DIR_NAMES:
            if blocked in target_parts_lower:
                return False, f"Systemverzeichnis blockiert: '{blocked}'"

        file_name_lower = resolved_target.name.lower()
        for keyword in BLOCKED_SENSITIVE_KEYWORDS:
            if keyword in file_name_lower:
                return False, f"Sicherheitsblockade: Enthält sensibles Schlüsselwort '{keyword}'"

        for part in target_parts_lower:
            if part in BLOCKED_ROBLOX_DIR_NAMES:
                return False, f"Geschütztes Roblox-Verzeichnis blockiert: '{part}'"

        if file_name_lower in BLOCKED_ROBLOX_FILENAMES:
            return False, f"Geschützte Roblox-Konfigurationsdatei blockiert: '{file_name_lower}'"

        if target_path.is_symlink():
            try:
                link_dest = target_path.readlink().resolve()
                if not any(cls._is_subpath_of(link_dest, root.resolve()) for root in allowed_roots):
                    return False, "Symlink verweist außerhalb der erlaubten Roblox-Verzeichnisse."
            except Exception:
                return False, "Symlink konnte nicht sicher aufgelöst werden."

        is_subpath = False
        for root in allowed_roots:
            try:
                resolved_root = root.resolve()
                if cls._is_subpath_of(resolved_target, resolved_root):
                    is_subpath = True
                    break
            except Exception:
                continue

        if not is_subpath:
            return False, "Pfad liegt außerhalb der autorisierten Roblox-Wurzelverzeichnisse."

        return True, "Sicher"

    @classmethod
    def is_safe_for_deletion(
        cls,
        file_path: Path,
        scanned_file_set: set[Path],
        allowed_roots: Iterable[Path],
    ) -> tuple[bool, str]:
        """Validate if a specific file can be safely deleted.

        Must pass all security checks AND be part of the scanned files list.
        """
        try:
            resolved = file_path.resolve()
        except Exception as exc:
            return False, f"Pfad kann nicht aufgelöst werden: {exc}"

        if file_path not in scanned_file_set and resolved not in scanned_file_set:
            return False, "Datei war nicht Teil des vorherigen Scan-Ergebnisses."

        is_safe, reason = cls.is_safe_roblox_target(resolved, allowed_roots)
        if not is_safe:
            return False, reason

        if not resolved.exists():
            return False, "Datei existiert nicht mehr."

        return True, "Bereit zum Löschen"

    @staticmethod
    def _is_subpath_of(child: Path, parent: Path) -> bool:
        """Helper to determine if child path is inside parent directory."""
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return False
