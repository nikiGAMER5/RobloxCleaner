"""Entry point for Roblox Cleaner desktop application."""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.config.settings import SettingsManager
from app.ui.main_window import MainWindow
from app.utils.logger import get_logger, setup_logger


def handle_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
    """Log uncaught global exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger = get_logger()
    logger.critical("Unbehandelte Ausnahme aufgetreten:", exc_info=(exc_type, exc_value, exc_traceback))


def main() -> int:
    """Main application lifecycle runner."""
    if sys.platform == "win32":
        try:
            app_id = "antigravity.robloxcleaner.app.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass

    setup_logger()
    logger = get_logger()
    logger.info("Roblox Cleaner wird gestartet...")

    sys.excepthook = handle_uncaught_exception

    app = QApplication(sys.argv)
    app.setApplicationName("Roblox Cleaner")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("RobloxCleaner")

    assets_dir = Path(__file__).resolve().parent / "assets"
    for icon_name in ("icon.ico", "icon.png", "icon.svg"):
        candidate = assets_dir / icon_name
        if candidate.exists():
            app.setWindowIcon(QIcon(str(candidate)))
            break

    settings_manager = SettingsManager()
    window = MainWindow(settings_manager)
    window.show()

    logger.info("Hauptfenster erfolgreich initialisiert.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
