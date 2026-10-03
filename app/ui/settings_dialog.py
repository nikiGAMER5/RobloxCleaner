"""Settings dialog allowing users to customize preferences, backups, and scan scope."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import AppSettings, SettingsManager
from app.scanner.roblox_paths import get_all_categories
from app.utils.logger import get_log_file_path, read_recent_logs


class SettingsDialog(QDialog):
    """Configuration dialog for Roblox Cleaner."""

    def __init__(self, settings_manager: SettingsManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.current_settings = settings_manager.get()
        self.category_checkboxes: Dict[str, QCheckBox] = {}
        is_en = self.current_settings.language == "en"

        self.setWindowTitle("Settings - Roblox Cleaner" if is_en else "Einstellungen - Roblox Cleaner")
        self.resize(560, 500)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(16)

        tabs = QTabWidget()

        tab_general = QWidget()
        general_layout = QVBoxLayout(tab_general)
        general_layout.setSpacing(14)

        self.cb_confirm = QCheckBox(
            "Require confirmation before cleaning" if is_en else "Vor dem Bereinigen Bestätigung verlangen"
        )
        self.cb_confirm.setChecked(self.current_settings.confirm_before_clean)
        general_layout.addWidget(self.cb_confirm)

        self.cb_warn_roblox = QCheckBox(
            "Warn if Roblox is currently running" if is_en else "Warnen, wenn Roblox noch geöffnet ist"
        )
        self.cb_warn_roblox.setChecked(self.current_settings.warn_roblox_running)
        general_layout.addWidget(self.cb_warn_roblox)

        backup_group = QGroupBox("Safety Backup" if is_en else "Sicherheits-Backup")
        backup_layout = QVBoxLayout(backup_group)
        backup_layout.setSpacing(10)

        self.cb_backup = QCheckBox(
            "Archive files to a ZIP backup before deleting"
            if is_en
            else "Dateien vor dem Löschen als ZIP sichern"
        )
        self.cb_backup.setChecked(self.current_settings.backup_enabled)
        backup_layout.addWidget(self.cb_backup)

        path_box = QHBoxLayout()
        self.edit_backup_path = QLineEdit(self.current_settings.backup_dir)
        self.edit_backup_path.setPlaceholderText(
            "Path to backup folder..." if is_en else "Pfad zum Backup-Verzeichnis..."
        )
        self.btn_browse = QPushButton("Browse..." if is_en else "Durchsuchen...")
        self.btn_browse.setObjectName("secondaryBtn")
        self.btn_browse.clicked.connect(self._browse_backup_dir)
        path_box.addWidget(self.edit_backup_path)
        path_box.addWidget(self.btn_browse)
        backup_layout.addLayout(path_box)

        general_layout.addWidget(backup_group)

        app_folder_group = QGroupBox("Application Location" if is_en else "Anwendungs-Verzeichnis")
        app_folder_layout = QHBoxLayout(app_folder_group)
        app_dir_path = Path(__file__).resolve().parent.parent.parent
        self.lbl_app_path = QLabel(str(app_dir_path))
        self.lbl_app_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_app_path.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.btn_open_app_dir = QPushButton("Open Folder" if is_en else "Ordner öffnen")
        self.btn_open_app_dir.setObjectName("secondaryBtn")
        self.btn_open_app_dir.clicked.connect(lambda: self._open_dir(app_dir_path))
        app_folder_layout.addWidget(self.lbl_app_path, stretch=1)
        app_folder_layout.addWidget(self.btn_open_app_dir)
        general_layout.addWidget(app_folder_group)

        ui_group = QGroupBox("Appearance & Language" if is_en else "Erscheinungsbild & Sprache")
        ui_layout = QVBoxLayout(ui_group)
        ui_layout.setSpacing(10)

        theme_box = QHBoxLayout()
        theme_lbl = QLabel("Color Theme:" if is_en else "Farbschema (Theme):")
        self.combo_theme = QComboBox()
        self.combo_theme.addItem("Dark Modern", "dark")
        self.combo_theme.addItem("OLED Midnight", "deep_black")
        self.combo_theme.addItem("Cyber Blue", "cyber_blue")
        idx = self.combo_theme.findData(self.current_settings.theme)
        if idx >= 0:
            self.combo_theme.setCurrentIndex(idx)
        theme_box.addWidget(theme_lbl)
        theme_box.addWidget(self.combo_theme)
        ui_layout.addLayout(theme_box)

        lang_box = QHBoxLayout()
        lang_lbl = QLabel("Language / Sprache:")
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("English", "en")
        self.combo_lang.addItem("Deutsch", "de")
        idx_lang = self.combo_lang.findData(self.current_settings.language)
        if idx_lang >= 0:
            self.combo_lang.setCurrentIndex(idx_lang)
        lang_box.addWidget(lang_lbl)
        lang_box.addWidget(self.combo_lang)
        ui_layout.addLayout(lang_box)

        general_layout.addWidget(ui_group)
        general_layout.addStretch()
        tabs.addTab(tab_general, "General" if is_en else "Allgemein")

        tab_categories = QWidget()
        cat_layout = QVBoxLayout(tab_categories)
        cat_layout.setSpacing(12)

        cat_info = QLabel(
            "Select which Roblox areas should be scanned and cleaned:"
            if is_en
            else "Wähle aus, welche Roblox-Bereiche beim Scan berücksichtigt werden:"
        )
        cat_info.setWordWrap(True)
        cat_layout.addWidget(cat_info)

        all_cats = get_all_categories()
        enabled_map = self.current_settings.enabled_categories

        for cat in all_cats:
            label_text = f"{cat.name_en} ({cat.description_en})" if is_en else f"{cat.name_de} ({cat.description_de})"
            box = QCheckBox(label_text)
            box.setChecked(enabled_map.get(cat.id, True))
            self.category_checkboxes[cat.id] = box
            cat_layout.addWidget(box)

        cat_layout.addStretch()
        tabs.addTab(tab_categories, "Scan Targets" if is_en else "Scan-Ziele")

        tab_logs = QWidget()
        logs_layout = QVBoxLayout(tab_logs)
        logs_layout.setSpacing(10)

        log_path_lbl = QLabel(f"Log File: {get_log_file_path()}" if is_en else f"Logdatei: {get_log_file_path()}")
        log_path_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        log_path_lbl.setWordWrap(True)
        logs_layout.addWidget(log_path_lbl)

        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setPlainText(read_recent_logs())
        self.log_viewer.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        logs_layout.addWidget(self.log_viewer)

        log_btn_bar = QHBoxLayout()
        btn_refresh_log = QPushButton("Refresh" if is_en else "Aktualisieren")
        btn_refresh_log.setObjectName("secondaryBtn")
        btn_refresh_log.clicked.connect(lambda: self.log_viewer.setPlainText(read_recent_logs()))

        btn_open_log = QPushButton("Open Log File" if is_en else "Logdatei öffnen")
        btn_open_log.setObjectName("secondaryBtn")
        btn_open_log.clicked.connect(self._open_log_file)

        log_btn_bar.addWidget(btn_refresh_log)
        log_btn_bar.addWidget(btn_open_log)
        log_btn_bar.addStretch()
        logs_layout.addLayout(log_btn_bar)

        tabs.addTab(tab_logs, "Logs" if is_en else "Protokolle")

        main_layout.addWidget(tabs)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel" if is_en else "Abbrechen")
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save" if is_en else "Speichern")
        btn_save.setObjectName("scanBtn")
        btn_save.clicked.connect(self._save_and_close)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        main_layout.addLayout(btn_box)

    def _browse_backup_dir(self) -> None:
        """Open directory picker for backup location."""
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder", self.edit_backup_path.text())
        if folder:
            self.edit_backup_path.setText(folder)

    def _open_dir(self, directory: Path) -> None:
        """Open given directory in Windows Explorer."""
        if directory.exists():
            try:
                os.startfile(str(directory))
            except Exception:
                pass

    def _open_log_file(self) -> None:
        """Open log file in system default viewer."""
        path = get_log_file_path()
        if path.exists():
            try:
                os.startfile(str(path))
            except Exception:
                pass

    def _save_and_close(self) -> None:
        """Save settings and apply."""
        cat_map = {cat_id: cb.isChecked() for cat_id, cb in self.category_checkboxes.items()}

        new_settings = AppSettings(
            confirm_before_clean=self.cb_confirm.isChecked(),
            warn_roblox_running=self.cb_warn_roblox.isChecked(),
            backup_enabled=self.cb_backup.isChecked(),
            backup_dir=self.edit_backup_path.text().strip(),
            theme=self.combo_theme.currentData(),
            language=self.combo_lang.currentData(),
            enabled_categories=cat_map,
        )

        self.settings_manager.save(new_settings)
        self.accept()
