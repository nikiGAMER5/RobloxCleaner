"""Cleaning engine responsible for safely removing validated Roblox files."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from PySide6.QtCore import QObject, Signal

from app.cleaner.backup import BackupManager
from app.scanner.roblox_paths import get_allowed_roblox_roots
from app.scanner.scanner import ScannedFile, ScanResult
from app.utils.logger import get_logger
from app.utils.security import SecurityValidator


@dataclass
class CleanResult:
    """Summary metrics of a completed cleaning operation."""

    processed_count: int = 0
    deleted_count: int = 0
    failed_count: int = 0
    freed_bytes: int = 0
    failed_files: List[Tuple[Path, str]] = field(default_factory=list)
    backup_path: Optional[Path] = None
    cancelled: bool = False


class RobloxCleaner(QObject):
    """Safely cleans scanned and verified Roblox files with progress reporting."""

    clean_started = Signal()
    progress = Signal(int, str)
    file_cleaned = Signal(str, "qint64")
    clean_finished = Signal(object)
    clean_error = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger()
        self._is_cancelled = False

    def cancel(self) -> None:
        """Cancel current cleaning process."""
        self._is_cancelled = True

    def clean(
        self,
        scan_result: ScanResult,
        selected_category_ids: Optional[Set[str]] = None,
        backup_enabled: bool = False,
        backup_dir: Optional[Path] = None,
    ) -> CleanResult:
        """Perform the cleaning operation on selected categories from the scan result."""
        self._is_cancelled = False
        self.clean_started.emit()
        self.logger.info("Roblox-Bereinigung gestartet.")

        allowed_roots = get_allowed_roblox_roots()
        scanned_set = scan_result.scanned_file_paths

        files_to_clean: List[ScannedFile] = []
        for cat_id, cat_data in scan_result.categories.items():
            if selected_category_ids is None or cat_id in selected_category_ids:
                files_to_clean.extend(cat_data.files)

        total_files = len(files_to_clean)
        clean_result = CleanResult(processed_count=total_files)

        if total_files == 0:
            self.progress.emit(100, "Keine Dateien zum Bereinigen ausgewählt.")
            self.clean_finished.emit(clean_result)
            return clean_result

        if backup_enabled and backup_dir:
            self.progress.emit(0, "Erstelle Sicherheits-Backup...")
            bm = BackupManager(backup_dir)
            ok, b_path, b_msg = bm.create_backup(
                files_to_clean,
                progress_callback=lambda pct, msg: self.progress.emit(int(pct * 0.3), msg),
            )
            clean_result.backup_path = b_path
            if not ok:
                self.logger.warning(f"Backup-Warnung: {b_msg}. Bereinigung wird dennoch fortgesetzt.")

        dirs_to_prune: Set[Path] = set()

        for idx, file_obj in enumerate(files_to_clean):
            if self._is_cancelled:
                self.logger.info("Bereinigung wurde vom Benutzer abgebrochen.")
                clean_result.cancelled = True
                break

            pct_base = 30 if backup_enabled else 0
            pct_span = 70 if backup_enabled else 100
            current_pct = pct_base + int(((idx + 1) / total_files) * pct_span)

            file_path = file_obj.path
            self.progress.emit(current_pct, f"Bereinige: {file_path.name}")

            is_safe, reason = SecurityValidator.is_safe_for_deletion(file_path, scanned_set, allowed_roots)
            if not is_safe:
                self.logger.warning(f"Datei übersprungen aus Sicherheitsgründen ({reason}): {file_path}")
                clean_result.failed_count += 1
                clean_result.failed_files.append((file_path, f"Sicherheitsblockade: {reason}"))
                continue

            deleted, err_msg = self._delete_single_file(file_path)
            if deleted:
                clean_result.deleted_count += 1
                clean_result.freed_bytes += file_obj.size
                self.file_cleaned.emit(file_path.name, file_obj.size)
                dirs_to_prune.add(file_path.parent)
            else:
                clean_result.failed_count += 1
                clean_result.failed_files.append((file_path, err_msg))
                self.logger.debug(f"Konnte Datei nicht löschen: {file_path} ({err_msg})")

        self._prune_empty_dirs(dirs_to_prune, allowed_roots)

        self.progress.emit(100, "Bereinigung abgeschlossen.")
        self.logger.info(
            f"Bereinigung abgeschlossen. Erfolgreich: {clean_result.deleted_count}, "
            f"Fehlgeschlagen: {clean_result.failed_count}, "
            f"Freigegeben: {clean_result.freed_bytes} Bytes."
        )

        self.clean_finished.emit(clean_result)
        return clean_result

    def _delete_single_file(self, file_path: Path) -> Tuple[bool, str]:
        """Safely delete a single file with friendly Windows error handling."""
        try:
            if not file_path.exists():
                return True, "Datei existierte bereits nicht mehr"

            try:
                os.chmod(file_path, 0o777)
            except Exception:
                pass

            file_path.unlink()
            return True, ""
        except PermissionError:
            return False, "Datei ist durch Roblox oder einen anderen Prozess gesperrt."
        except FileNotFoundError:
            return True, ""
        except Exception as exc:
            return False, str(exc)

    def _prune_empty_dirs(self, directories: Set[Path], allowed_roots: Set[Path]) -> None:
        """Safely remove empty temporary subdirectories."""
        for directory in directories:
            try:
                if directory in allowed_roots:
                    continue

                is_safe, _ = SecurityValidator.is_safe_roblox_target(directory, allowed_roots)
                if not is_safe:
                    continue

                if directory.exists() and directory.is_dir():
                    if not any(directory.iterdir()):
                        directory.rmdir()
                        self.logger.debug(f"Leeres temporäres Verzeichnis entfernt: {directory}")
            except Exception:
                pass
