"""Scanner engine for discovering safe Roblox temporary and cache files."""

from __future__ import annotations

import datetime
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from PySide6.QtCore import QObject, Signal

from app.scanner.roblox_paths import get_all_categories, get_allowed_roblox_roots, RobloxCategory
from app.utils.logger import get_logger
from app.utils.security import SecurityValidator, BLOCKED_ROBLOX_FILENAMES, BLOCKED_SENSITIVE_KEYWORDS


@dataclass
class ScannedFile:
    """Represents an individual file detected during scan."""

    path: Path
    size: int
    category_id: str
    category_name: str
    modified_time: float


@dataclass
class CategoryScanResult:
    """Aggregated scan findings for a specific category."""

    category_id: str
    category_name: str
    icon_name: str
    file_count: int = 0
    total_size: int = 0
    files: List[ScannedFile] = field(default_factory=list)


@dataclass
class ScanResult:
    """Complete summary result of a scan operation."""

    categories: Dict[str, CategoryScanResult] = field(default_factory=dict)
    total_files: int = 0
    total_size: int = 0
    scanned_file_paths: Set[Path] = field(default_factory=set)
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

    def get_category_files(self, category_id: str) -> List[ScannedFile]:
        """Return files for a specific category."""
        if category_id in self.categories:
            return self.categories[category_id].files
        return []


class RobloxScanner(QObject):
    """High-performance thread-safe Roblox directory scanner with Qt signals."""

    scan_started = Signal()
    progress = Signal(int, str)
    category_scanned = Signal(str, int, "qint64")
    scan_finished = Signal(object)
    scan_error = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger()
        self._is_cancelled = False

    def cancel(self) -> None:
        """Request cancellation of current scan."""
        self._is_cancelled = True

    def scan(self, enabled_categories: Optional[Dict[str, bool]] = None, language: str = "de") -> ScanResult:
        """Perform high-speed scan across enabled Roblox categories."""
        self._is_cancelled = False
        self.scan_started.emit()
        self.logger.info("Roblox-Scan gestartet.")

        categories = get_all_categories()
        allowed_roots = get_allowed_roblox_roots()

        if enabled_categories:
            categories = [c for c in categories if enabled_categories.get(c.id, True)]

        result = ScanResult()
        total_cats = max(len(categories), 1)

        for idx, category in enumerate(categories):
            if self._is_cancelled:
                self.logger.info("Scan wurde vom Benutzer abgebrochen.")
                break

            cat_name = category.name_de if language == "de" else category.name_en
            progress_pct = int((idx / total_cats) * 100)
            self.progress.emit(progress_pct, f"Scanne {cat_name}...")

            cat_result = CategoryScanResult(
                category_id=category.id,
                category_name=cat_name,
                icon_name=category.icon_name,
            )

            targets = category.resolve_targets()
            for target in targets:
                if self._is_cancelled:
                    break

                if not target.exists():
                    continue

                if target.is_file():
                    self._check_and_add_path(target, category, cat_name, allowed_roots, cat_result, result)
                elif target.is_dir():
                    self._scan_directory_fast(str(target), category, cat_name, allowed_roots, cat_result, result)

            result.categories[category.id] = cat_result
            result.total_files += cat_result.file_count
            result.total_size += cat_result.total_size
            self.category_scanned.emit(category.id, cat_result.file_count, cat_result.total_size)

        self.progress.emit(100, "Scan abgeschlossen.")
        self.logger.info(
            f"Scan abgeschlossen. Gefunden: {result.total_files} Dateien ({result.total_size} Bytes)."
        )
        self.scan_finished.emit(result)
        return result

    def _scan_directory_fast(
        self,
        directory_str: str,
        category: RobloxCategory,
        cat_name: str,
        allowed_roots: Set[Path],
        cat_result: CategoryScanResult,
        result: ScanResult,
    ) -> None:
        """Scan a directory tree using low-overhead os.scandir."""
        dir_path = Path(directory_str)
        is_safe, reason = SecurityValidator.is_safe_roblox_target(dir_path, allowed_roots)
        if not is_safe:
            self.logger.warning(f"Verzeichnis übersprungen ({reason}): {directory_str}")
            return

        stack = [directory_str]
        while stack and not self._is_cancelled:
            current_dir = stack.pop()
            try:
                with os.scandir(current_dir) as it:
                    for entry in it:
                        if self._is_cancelled:
                            break

                        if entry.is_symlink():
                            continue

                        if entry.is_dir(follow_symlinks=False):
                            if category.recursive:
                                name_lower = entry.name.lower()
                                if name_lower not in {"versions", "clientsettings", "localstorage"}:
                                    stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            name_lower = entry.name.lower()
                            if name_lower in BLOCKED_ROBLOX_FILENAMES:
                                continue
                            if any(kw in name_lower for kw in BLOCKED_SENSITIVE_KEYWORDS):
                                continue

                            try:
                                stat_info = entry.stat(follow_symlinks=False)
                                f_size = stat_info.st_size
                                f_mtime = stat_info.st_mtime

                                p = Path(entry.path)
                                scanned_file = ScannedFile(
                                    path=p,
                                    size=f_size,
                                    category_id=category.id,
                                    category_name=cat_name,
                                    modified_time=f_mtime,
                                )
                                cat_result.files.append(scanned_file)
                                cat_result.file_count += 1
                                cat_result.total_size += f_size

                                result.scanned_file_paths.add(p)
                            except (PermissionError, FileNotFoundError):
                                pass
            except (PermissionError, FileNotFoundError):
                continue
            except Exception as exc:
                self.logger.debug(f"Fehler in {current_dir}: {exc}")

    def _check_and_add_path(
        self,
        file_path: Path,
        category: RobloxCategory,
        cat_name: str,
        allowed_roots: Set[Path],
        cat_result: CategoryScanResult,
        result: ScanResult,
    ) -> None:
        """Validate and append an individual single file target."""
        try:
            if file_path.is_symlink():
                return

            is_safe, _ = SecurityValidator.is_safe_roblox_target(file_path, allowed_roots)
            if not is_safe:
                return

            name_lower = file_path.name.lower()
            if name_lower in BLOCKED_ROBLOX_FILENAMES:
                return
            if any(kw in name_lower for kw in BLOCKED_SENSITIVE_KEYWORDS):
                return

            stat = file_path.stat()
            file_size = stat.st_size
            mtime = stat.st_mtime

            scanned_file = ScannedFile(
                path=file_path,
                size=file_size,
                category_id=category.id,
                category_name=cat_name,
                modified_time=mtime,
            )

            cat_result.files.append(scanned_file)
            cat_result.file_count += 1
            cat_result.total_size += file_size
            result.scanned_file_paths.add(file_path)
        except Exception:
            pass
