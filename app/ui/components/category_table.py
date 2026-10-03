"""Table component presenting detected categories, file counts, and sizes."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Set

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.scanner.roblox_paths import get_all_categories
from app.scanner.scanner import CategoryScanResult, ScanResult
from app.ui.components.file_viewer_dialog import FileViewerDialog
from app.utils.helpers import format_bytes, get_local_appdata, get_temp_dir
from app.utils.i18n import tr


class CategoryTableWidget(QWidget):
    """Table for displaying discovered categories with checkboxes and size metrics."""

    selection_changed = Signal(int, "qint64")

    def __init__(self, lang: str = "en", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.lang = lang
        self.scan_result: Optional[ScanResult] = None
        self.checkboxes: Dict[str, QCheckBox] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        self.btn_select_all = QPushButton(tr("btn_select_all", self.lang))
        self.btn_select_all.setObjectName("secondaryBtn")
        self.btn_select_all.clicked.connect(lambda: self.set_all_selected(True))

        self.btn_deselect_all = QPushButton(tr("btn_deselect_all", self.lang))
        self.btn_deselect_all.setObjectName("secondaryBtn")
        self.btn_deselect_all.clicked.connect(lambda: self.set_all_selected(False))

        top_bar.addWidget(self.btn_select_all)
        top_bar.addWidget(self.btn_deselect_all)
        top_bar.addStretch()

        layout.addLayout(top_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.update_headers()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QTableWidget.NoSelection)

        layout.addWidget(self.table)

    def update_headers(self) -> None:
        """Update header column titles according to current language."""
        self.table.setHorizontalHeaderLabels([
            tr("col_category", self.lang),
            tr("col_files", self.lang),
            tr("col_size", self.lang),
            tr("col_actions", self.lang),
        ])

    def update_language(self, lang: str) -> None:
        """Update language strings in table."""
        self.lang = lang
        self.btn_select_all.setText(tr("btn_select_all", self.lang))
        self.btn_deselect_all.setText(tr("btn_deselect_all", self.lang))
        self.update_headers()
        if self.scan_result:
            self.load_scan_result(self.scan_result)

    def load_scan_result(self, scan_result: ScanResult) -> None:
        """Populate the table with category results."""
        self.scan_result = scan_result
        self.checkboxes.clear()
        self.table.setRowCount(0)

        row_index = 0
        for cat_id, cat_data in scan_result.categories.items():
            self.table.insertRow(row_index)
            self.table.setRowHeight(row_index, 46)

            check_widget = QWidget()
            check_layout = QHBoxLayout(check_widget)
            check_layout.setContentsMargins(12, 0, 8, 0)
            check_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            cb = QCheckBox(cat_data.category_name)
            cb.setChecked(cat_data.file_count > 0)
            cb.stateChanged.connect(self._on_check_state_changed)
            check_layout.addWidget(cb)
            self.checkboxes[cat_id] = cb
            self.table.setCellWidget(row_index, 0, check_widget)

            files_suffix = "Files" if self.lang == "en" else "Dateien"
            files_item = QTableWidgetItem(f"{cat_data.file_count} {files_suffix}")
            files_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_index, 1, files_item)

            size_item = QTableWidgetItem(format_bytes(cat_data.total_size))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_index, 2, size_item)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(6, 0, 10, 0)
            actions_layout.setSpacing(6)
            actions_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            folder_btn = QPushButton(tr("btn_folder", self.lang))
            folder_btn.setObjectName("tableActionBtn")
            folder_btn.setToolTip("Open folder in Explorer" if self.lang == "en" else "Ordner im Explorer öffnen")
            folder_btn.clicked.connect(lambda _, cid=cat_id, c=cat_data: self._open_category_folder(cid, c))
            actions_layout.addWidget(folder_btn)

            detail_btn = QPushButton(tr("btn_inspect", self.lang))
            detail_btn.setObjectName("tableActionBtn")
            detail_btn.setEnabled(cat_data.file_count > 0)
            detail_btn.setToolTip("View files" if self.lang == "en" else "Dateien ansehen")
            detail_btn.clicked.connect(lambda _, c=cat_data: self._show_details(c))
            actions_layout.addWidget(detail_btn)

            self.table.setCellWidget(row_index, 3, actions_widget)

            row_index += 1

        self._on_check_state_changed()

    def _open_category_folder(self, cat_id: str, category_data: CategoryScanResult) -> None:
        """Open the specific category folder on disk in Windows Explorer."""
        target_dir: Optional[Path] = None

        if category_data.files:
            first_path = category_data.files[0].path
            target_dir = first_path.parent if first_path.is_file() else first_path

        if not target_dir or not target_dir.exists():
            for cat in get_all_categories():
                if cat.id == cat_id:
                    for t in cat.resolve_targets():
                        if t.is_dir() and t.exists():
                            target_dir = t
                            break
                        elif t.is_file() and t.parent.is_dir() and t.parent.exists():
                            target_dir = t.parent
                            break
                    break

        if not target_dir or not target_dir.exists():
            local_roblox = get_local_appdata() / "Roblox"
            temp_roblox = get_temp_dir() / "Roblox"
            target_dir = local_roblox if local_roblox.exists() else temp_roblox

        if target_dir and target_dir.exists():
            try:
                os.startfile(str(target_dir))
            except Exception:
                pass

    def _show_details(self, category_data: CategoryScanResult) -> None:
        """Open modal to view individual files in this category."""
        dialog = FileViewerDialog(category_data.category_name, category_data.files, lang=self.lang, parent=self)
        dialog.exec()

    def _on_check_state_changed(self) -> None:
        """Calculate selected files and sizes and notify listeners."""
        if not self.scan_result:
            self.selection_changed.emit(0, 0)
            return

        total_files = 0
        total_bytes = 0

        for cat_id, cb in self.checkboxes.items():
            if cb.isChecked() and cat_id in self.scan_result.categories:
                cat_data = self.scan_result.categories[cat_id]
                total_files += cat_data.file_count
                total_bytes += cat_data.total_size

        self.selection_changed.emit(total_files, total_bytes)

    def get_selected_category_ids(self) -> Set[str]:
        """Return the set of category IDs currently checked by the user."""
        return {cat_id for cat_id, cb in self.checkboxes.items() if cb.isChecked()}

    def set_all_selected(self, select: bool) -> None:
        """Check or uncheck all category checkboxes."""
        for cb in self.checkboxes.values():
            cb.setChecked(select)
