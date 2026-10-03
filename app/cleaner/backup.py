"""Backup manager for creating safe archives of Roblox files prior to cleaning."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Callable, List, Optional
import zipfile

from app.scanner.scanner import ScannedFile
from app.utils.logger import get_logger


class BackupManager:
    """Creates compressed zip archives of scanned files before deletion."""

    def __init__(self, backup_directory: Path) -> None:
        self.backup_dir = backup_directory
        self.logger = get_logger()

    def create_backup(
        self,
        files: List[ScannedFile],
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> tuple[bool, Path | None, str]:
        """Compress given files into a timestamped zip archive.

        Returns:
            (success: bool, archive_path: Optional[Path], message: str)
        """
        if not files:
            return True, None, "Keine Dateien zum Sichern vorhanden."

        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_path = self.backup_dir / f"roblox_backup_{timestamp}.zip"

            self.logger.info(f"Erstelle Backup für {len(files)} Dateien in {archive_path}...")
            total = len(files)

            with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for idx, file_obj in enumerate(files):
                    fpath = file_obj.path
                    if fpath.exists() and fpath.is_file():
                        try:
                            arcname = f"{file_obj.category_id}/{fpath.name}"
                            zf.write(fpath, arcname=arcname)
                        except Exception as exc:
                            self.logger.warning(f"Backup-Warnung für {fpath}: {exc}")

                    if progress_callback:
                        pct = int(((idx + 1) / total) * 100)
                        progress_callback(pct, f"Sichere: {fpath.name}")

            self.logger.info(f"Backup erfolgreich erstellt: {archive_path}")
            return True, archive_path, f"Backup erfolgreich gesichert ({archive_path.name})"
        except Exception as exc:
            err_msg = f"Backup fehlgeschlagen: {exc}"
            self.logger.error(err_msg)
            return False, None, err_msg
