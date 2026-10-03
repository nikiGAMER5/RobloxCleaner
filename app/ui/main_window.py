"""Main application window for Roblox Cleaner."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Set

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.cleaner.cleaner import CleanResult, RobloxCleaner
from app.cleaner.process_manager import RobloxProcessManager
from app.config.settings import SettingsManager
from app.scanner.scanner import RobloxScanner, ScanResult
from app.ui.components.category_table import CategoryTableWidget
from app.ui.components.process_banner import ProcessBanner
from app.ui.components.stat_card import StatCard
from app.ui.settings_dialog import SettingsDialog
from app.ui.styles import get_stylesheet
from app.utils.helpers import format_bytes, get_local_appdata, get_temp_dir
from app.utils.i18n import tr
from app.utils.logger import get_logger


class ScanWorker(QThread):
    """Background worker thread for non-blocking file system scanning."""

    progress = Signal(int, str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, scanner: RobloxScanner, enabled_categories: dict[str, bool], language: str) -> None:
        super().__init__()
        self.scanner = scanner
        self.enabled_categories = enabled_categories
        self.language = language

    def run(self) -> None:
        try:
            self.scanner.progress.connect(self.progress.emit)
            result = self.scanner.scan(self.enabled_categories, self.language)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


class CleanWorker(QThread):
    """Background worker thread for non-blocking file deletion."""

    progress = Signal(int, str)
    file_cleaned = Signal(str, "qint64")
    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        cleaner: RobloxCleaner,
        scan_result: ScanResult,
        selected_categories: Set[str],
        backup_enabled: bool,
        backup_dir: Path,
    ) -> None:
        super().__init__()
        self.cleaner = cleaner
        self.scan_result = scan_result
        self.selected_categories = selected_categories
        self.backup_enabled = backup_enabled
        self.backup_dir = backup_dir

    def run(self) -> None:
        try:
            self.cleaner.progress.connect(self.progress.emit)
            self.cleaner.file_cleaned.connect(self.file_cleaned.emit)
            result = self.cleaner.clean(
                scan_result=self.scan_result,
                selected_category_ids=self.selected_categories,
                backup_enabled=self.backup_enabled,
                backup_dir=self.backup_dir,
            )
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    """Main application window presenting scan, clean, and preview features."""

    def __init__(self, settings_manager: SettingsManager) -> None:
        super().__init__()
        self.settings_manager = settings_manager
        self.logger = get_logger()

        self.scanner = RobloxScanner()
        self.cleaner = RobloxCleaner()
        self.process_manager = RobloxProcessManager()

        self.last_scan_result: Optional[ScanResult] = None
        self.scan_worker: Optional[ScanWorker] = None
        self.clean_worker: Optional[CleanWorker] = None

        self.setWindowTitle("Roblox Cleaner")
        self.resize(880, 680)
        self.setMinimumSize(780, 560)

        self._init_ui()
        self.apply_theme()
        self.update_ui_texts()

        self.process_banner.check_status()

    def update_ui_texts(self) -> None:
        """Update all user-facing texts based on current language configuration."""
        lang = self.settings_manager.get().language
        self.title_label.setText(tr("app_title", lang))
        self.subtitle_label.setText(tr("app_subtitle", lang))
        self.btn_open_roblox_folder.setText(tr("btn_open_roblox_folder", lang))
        self._populate_roblox_menu()
        self.btn_open_folder.setText(tr("btn_open_folder", lang))
        self.btn_settings.setText(tr("settings", lang))
        self.card_files.set_title(tr("stat_files", lang))
        self.card_total_space.set_title(tr("stat_used", lang))
        self.card_reclaimable.set_title(tr("stat_reclaimable", lang))
        self.cat_title.setText(tr("section_categories", lang))
        self.btn_scan.setText(tr("btn_scan", lang))
        self.btn_clean.setText(tr("btn_clean", lang))
        self.btn_cancel.setText(tr("btn_cancel", lang))
        self.category_table.update_language(lang)
        self.process_banner.update_language(lang)

    def _init_ui(self) -> None:
        """Construct the entire user interface hierarchy."""
        lang = self.settings_manager.get().language
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        header_layout = QHBoxLayout()

        title_container = QVBoxLayout()
        title_container.setSpacing(2)

        title_row = QHBoxLayout()
        logo_label = QLabel("⚡")
        logo_label.setStyleSheet("font-size: 24px;")
        title_row.addWidget(logo_label)

        self.title_label = QLabel(tr("app_title", lang))
        self.title_label.setObjectName("appTitle")
        title_row.addWidget(self.title_label)
        title_row.addStretch()

        self.subtitle_label = QLabel(tr("app_subtitle", lang))
        self.subtitle_label.setObjectName("appSubtitle")

        title_container.addLayout(title_row)
        title_container.addWidget(self.subtitle_label)
        header_layout.addLayout(title_container)

        header_layout.addStretch()

        self.btn_open_roblox_folder = QPushButton(tr("btn_open_roblox_folder", lang))
        self.btn_open_roblox_folder.setObjectName("secondaryBtn")
        self.roblox_menu = QMenu(self)
        self.btn_open_roblox_folder.setMenu(self.roblox_menu)
        self._populate_roblox_menu()
        header_layout.addWidget(self.btn_open_roblox_folder)

        self.btn_open_folder = QPushButton(tr("btn_open_folder", lang))
        self.btn_open_folder.setObjectName("secondaryBtn")
        self.btn_open_folder.clicked.connect(self._open_project_folder)
        header_layout.addWidget(self.btn_open_folder)

        self.btn_settings = QPushButton(tr("settings", lang))
        self.btn_settings.setObjectName("secondaryBtn")
        self.btn_settings.clicked.connect(self._open_settings)
        header_layout.addWidget(self.btn_settings)

        main_layout.addLayout(header_layout)

        self.process_banner = ProcessBanner(lang=lang)
        main_layout.addWidget(self.process_banner)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)

        self.card_files = StatCard(tr("stat_files", lang), "0", tr("stat_files_sub_none", lang))
        self.card_total_space = StatCard(tr("stat_used", lang), "0 B", tr("stat_used_sub", lang))
        self.card_reclaimable = StatCard(
            tr("stat_reclaimable", lang), "0 B", tr("stat_reclaimable_sub", lang, count=0), accent_color="#00E676"
        )

        stats_layout.addWidget(self.card_files)
        stats_layout.addWidget(self.card_total_space)
        stats_layout.addWidget(self.card_reclaimable)

        main_layout.addLayout(stats_layout)

        category_header = QHBoxLayout()
        self.cat_title = QLabel(tr("section_categories", lang))
        self.cat_title.setObjectName("sectionHeader")
        category_header.addWidget(self.cat_title)
        category_header.addStretch()
        main_layout.addLayout(category_header)

        self.category_table = CategoryTableWidget(lang=lang)
        self.category_table.selection_changed.connect(self._on_table_selection_changed)
        main_layout.addWidget(self.category_table, stretch=1)

        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(6)

        status_row = QHBoxLayout()
        self.status_label = QLabel(tr("status_ready", lang))
        self.status_label.setObjectName("statusLabel")
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        self.pct_label = QLabel("")
        self.pct_label.setObjectName("statusLabel")
        status_row.addWidget(self.pct_label)

        progress_layout.addLayout(status_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        progress_layout.addWidget(self.progress_bar)

        main_layout.addLayout(progress_layout)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(14)

        self.btn_scan = QPushButton(tr("btn_scan", lang))
        self.btn_scan.setObjectName("scanBtn")
        self.btn_scan.clicked.connect(self.start_scan)
        action_layout.addWidget(self.btn_scan)

        self.btn_clean = QPushButton(tr("btn_clean", lang))
        self.btn_clean.setObjectName("cleanBtn")
        self.btn_clean.setEnabled(False)
        self.btn_clean.clicked.connect(self.start_clean)
        action_layout.addWidget(self.btn_clean)

        action_layout.addStretch()

        self.btn_cancel = QPushButton(tr("btn_cancel", lang))
        self.btn_cancel.setObjectName("secondaryBtn")
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel_active_task)
        action_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(action_layout)

    def apply_theme(self) -> None:
        """Load and apply current theme stylesheet."""
        theme_key = self.settings_manager.get().theme
        self.setStyleSheet(get_stylesheet(theme_key))

    def _open_settings(self) -> None:
        """Display settings dialog and reload styles and language on change."""
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec():
            self.apply_theme()
            self.update_ui_texts()

    def _open_project_folder(self) -> None:
        """Open the root folder where this project is located in Windows Explorer."""
        project_dir = Path(__file__).resolve().parent.parent.parent
        try:
            os.startfile(str(project_dir))
        except Exception as exc:
            self.logger.error(f"Failed to open directory: {exc}")

    def _populate_roblox_menu(self) -> None:
        """Create actions in the Roblox folders dropdown menu."""
        lang = self.settings_manager.get().language
        self.roblox_menu.clear()

        local_roblox = get_local_appdata() / "Roblox"
        act_appdata = self.roblox_menu.addAction(tr("menu_roblox_appdata", lang))
        act_appdata.triggered.connect(lambda: self._open_dir_safely(local_roblox))

        temp_roblox = get_temp_dir() / "Roblox"
        act_temp = self.roblox_menu.addAction(tr("menu_roblox_temp", lang))
        act_temp.triggered.connect(lambda: self._open_dir_safely(temp_roblox))

        logs_roblox = local_roblox / "logs"
        act_logs = self.roblox_menu.addAction(tr("menu_roblox_logs", lang))
        act_logs.triggered.connect(lambda: self._open_dir_safely(logs_roblox))

        dumps_roblox = get_local_appdata() / "CrashDumps"
        act_dumps = self.roblox_menu.addAction(tr("menu_crash_dumps", lang))
        act_dumps.triggered.connect(lambda: self._open_dir_safely(dumps_roblox))

        bloxstrap_dir = get_local_appdata() / "Bloxstrap"
        if bloxstrap_dir.exists():
            self.roblox_menu.addSeparator()
            act_blox = self.roblox_menu.addAction(tr("menu_bloxstrap", lang))
            act_blox.triggered.connect(lambda: self._open_dir_safely(bloxstrap_dir))

    def _open_dir_safely(self, path: Path) -> None:
        """Open a directory in Windows Explorer or create it if missing."""
        try:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            os.startfile(str(path))
        except Exception as exc:
            self.logger.error(f"Failed to open directory {path}: {exc}")

    def _set_ui_busy(self, is_busy: bool, operation_name: str = "") -> None:
        """Toggle button states during long running background tasks."""
        self.btn_scan.setEnabled(not is_busy)
        self.btn_clean.setEnabled(not is_busy and self.last_scan_result is not None)
        self.btn_settings.setEnabled(not is_busy)
        self.btn_cancel.setVisible(is_busy)

        if is_busy:
            self.progress_bar.setValue(0)
            self.status_label.setText(f"{operation_name} läuft...")
        else:
            self.pct_label.setText("")

    def _cancel_active_task(self) -> None:
        """Handle user cancellation request."""
        if self.scan_worker and self.scan_worker.isRunning():
            self.scanner.cancel()
            self.status_label.setText("Scan wird abgebrochen...")
        elif self.clean_worker and self.clean_worker.isRunning():
            self.cleaner.cancel()
            self.status_label.setText("Bereinigung wird abgebrochen...")

    def start_scan(self) -> None:
        """Initiate asynchronous scan of Roblox directories."""
        self._set_ui_busy(True, "Scan")
        self.status_label.setText("Suche Roblox-Verzeichnisse...")
        self.pct_label.setText("0%")

        settings = self.settings_manager.get()
        self.scan_worker = ScanWorker(
            scanner=self.scanner,
            enabled_categories=settings.enabled_categories,
            language=settings.language,
        )
        self.scan_worker.progress.connect(self._on_scan_progress)
        self.scan_worker.finished.connect(self._on_scan_finished)
        self.scan_worker.error.connect(self._on_scan_error)
        self.scan_worker.start()

    def _on_scan_progress(self, percent: int, message: str) -> None:
        """Update progress bar and status text."""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
        self.pct_label.setText(f"{percent}%")

    def _on_scan_finished(self, result: ScanResult) -> None:
        """Handle scan completion and update UI metrics."""
        self.last_scan_result = result
        self._set_ui_busy(False)
        self.progress_bar.setValue(100)

        lang = self.settings_manager.get().language

        self.card_files.set_value(str(result.total_files), tr("stat_files_sub_cats", lang, count=len(result.categories)))
        self.card_total_space.set_value(format_bytes(result.total_size), tr("stat_used_sub", lang))

        self.category_table.load_scan_result(result)

        if result.total_files == 0:
            self.status_label.setText(tr("status_clean_zero", lang))
            self.btn_clean.setEnabled(False)
        else:
            self.status_label.setText(
                tr("status_scan_done", lang, files=result.total_files, size=format_bytes(result.total_size))
            )
            self.btn_clean.setEnabled(True)

    def _on_scan_error(self, error_msg: str) -> None:
        """Handle scan errors gracefully."""
        self._set_ui_busy(False)
        self.status_label.setText(f"Scan error: {error_msg}")
        QMessageBox.critical(self, "Scan", f"{error_msg}")

    def _on_table_selection_changed(self, count: int, total_bytes: int) -> None:
        """Update reclaimable stat card when user checks/unchecks categories."""
        lang = self.settings_manager.get().language
        self.card_reclaimable.set_value(
            format_bytes(total_bytes),
            tr("stat_reclaimable_sub", lang, count=count),
        )
        self.btn_clean.setEnabled(count > 0 and not (self.scan_worker and self.scan_worker.isRunning()))

    def start_clean(self) -> None:
        """Validate safety, check Roblox status, confirm and launch cleaning."""
        if not self.last_scan_result:
            return

        selected_categories = self.category_table.get_selected_category_ids()
        if not selected_categories:
            QMessageBox.warning(self, "Roblox Cleaner", "Bitte wähle mindestens eine Kategorie zum Bereinigen aus.")
            return

        settings = self.settings_manager.get()
        lang = settings.language

        if settings.warn_roblox_running and self.process_manager.is_roblox_running():
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle(tr("warning_roblox_open_title", lang))
            msg_box.setText(tr("warning_roblox_open_text", lang))
            btn_close_and_clean = msg_box.addButton(tr("btn_close_and_clean", lang), QMessageBox.AcceptRole)
            btn_continue_anyway = msg_box.addButton(tr("btn_continue_anyway", lang), QMessageBox.ActionRole)
            btn_abort = msg_box.addButton(tr("btn_abort", lang), QMessageBox.RejectRole)

            msg_box.exec()
            clicked = msg_box.clickedButton()

            if clicked == btn_abort:
                return
            elif clicked == btn_close_and_clean:
                self.process_manager.terminate_roblox()
                self.process_banner.check_status()

        if settings.confirm_before_clean:
            total_selected_files = 0
            total_selected_bytes = 0
            for cid in selected_categories:
                if cid in self.last_scan_result.categories:
                    cdata = self.last_scan_result.categories[cid]
                    total_selected_files += cdata.file_count
                    total_selected_bytes += cdata.total_size

            backup_note = (
                tr("dialog_backup_note", lang, path=settings.backup_dir)
                if settings.backup_enabled
                else ""
            )

            confirm_text = tr(
                "dialog_confirm_text",
                lang,
                files=total_selected_files,
                size=format_bytes(total_selected_bytes),
            ) + backup_note

            confirm = QMessageBox.question(
                self,
                tr("dialog_confirm_title", lang),
                confirm_text,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if confirm != QMessageBox.Yes:
                return

        self._set_ui_busy(True, "Bereinigung" if lang == "de" else "Cleaning")
        self.progress_bar.setValue(0)
        self.pct_label.setText("0%")

        self.clean_worker = CleanWorker(
            cleaner=self.cleaner,
            scan_result=self.last_scan_result,
            selected_categories=selected_categories,
            backup_enabled=settings.backup_enabled,
            backup_dir=Path(settings.backup_dir),
        )
        self.clean_worker.progress.connect(self._on_clean_progress)
        self.clean_worker.finished.connect(self._on_clean_finished)
        self.clean_worker.error.connect(self._on_clean_error)
        self.clean_worker.start()

    def _on_clean_progress(self, percent: int, message: str) -> None:
        """Update progress during clean."""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
        self.pct_label.setText(f"{percent}%")

    def _on_clean_finished(self, result: CleanResult) -> None:
        """Display final results and summary dialog."""
        self._set_ui_busy(False)
        self.progress_bar.setValue(100)

        lang = self.settings_manager.get().language
        freed_str = format_bytes(result.freed_bytes)

        summary_text = tr(
            "dialog_clean_done_text",
            lang,
            processed=result.processed_count,
            deleted=result.deleted_count,
            freed=freed_str,
        )

        if result.backup_path:
            summary_text += tr("dialog_backup_note", lang, path=result.backup_path.name)

        if result.failed_count > 0:
            summary_text += tr("dialog_locked_files_note", lang, count=result.failed_count)

        self.status_label.setText(tr("status_clean_done", lang, freed=freed_str))

        QMessageBox.information(self, tr("dialog_clean_done_title", lang), summary_text)

        self.start_scan()

    def _on_clean_error(self, error_msg: str) -> None:
        """Handle errors during cleaning."""
        self._set_ui_busy(False)
        self.status_label.setText(f"Fehler bei Bereinigung: {error_msg}")
        QMessageBox.critical(self, "Fehler", f"Fehler beim Bereinigen:\n{error_msg}")
