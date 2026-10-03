"""Dialog to inspect individual scanned files inside a category."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.scanner.scanner import ScannedFile
from app.utils.helpers import format_bytes


class FileViewerDialog(QDialog):
    """Detailed inspector for files discovered in a given Roblox category."""

    def __init__(
        self,
        category_name: str,
        files: List[ScannedFile],
        lang: str = "en",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.lang = lang
        is_en = lang == "en"

        self.setWindowTitle(f"Files in: {category_name}" if is_en else f"Dateien in: {category_name}")
        self.resize(750, 480)
        self.files = files

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        top_bar = QHBoxLayout()
        header_text = (
            f"<b>{len(files)} files</b> discovered" if is_en else f"<b>{len(files)} Dateien</b> gefunden"
        )
        header_lbl = QLabel(header_text)
        header_lbl.setObjectName("sectionHeader")
        top_bar.addWidget(header_lbl)

        top_bar.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter / Search..." if is_en else "Filter / Suche...")
        self.search_input.setFixedWidth(220)
        self.search_input.textChanged.connect(self._filter_table)
        top_bar.addWidget(self.search_input)

        layout.addLayout(top_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["Filename", "Size", "Path"] if is_en else ["Dateiname", "Größe", "Pfad"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.setShowGrid(False)
        self.table.doubleClicked.connect(self._open_selected_folder)

        layout.addWidget(self.table)

        btn_bar = QHBoxLayout()
        self.open_folder_btn = QPushButton(
            "📁 Open Directory in Explorer" if is_en else "📁 Ordner im Explorer öffnen"
        )
        self.open_folder_btn.setObjectName("secondaryBtn")
        self.open_folder_btn.clicked.connect(self._open_selected_folder)
        btn_bar.addWidget(self.open_folder_btn)

        btn_bar.addStretch()

        close_btn = QPushButton("Close" if is_en else "Schließen")
        close_btn.setObjectName("secondaryBtn")
        close_btn.clicked.connect(self.accept)
        btn_bar.addWidget(close_btn)

        layout.addLayout(btn_bar)

        self._populate_table()

    def _populate_table(self) -> None:
        """Fill table with scanned files."""
        self.table.setRowCount(len(self.files))
        for row, f in enumerate(self.files):
            self.table.setRowHeight(row, 34)
            name_item = QTableWidgetItem(f.path.name)
            size_item = QTableWidgetItem(format_bytes(f.size))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            path_item = QTableWidgetItem(str(f.path))

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, size_item)
            self.table.setItem(row, 2, path_item)

    def _filter_table(self, query: str) -> None:
        """Filter table items by search query."""
        q = query.lower()
        for row in range(self.table.rowCount()):
            path_txt = self.table.item(row, 2).text().lower()
            name_txt = self.table.item(row, 0).text().lower()
            match = q in path_txt or q in name_txt
            self.table.setRowHidden(row, not match)

    def _open_selected_folder(self) -> None:
        """Open the directory containing the selected file in Windows Explorer."""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            file_path_str = self.table.item(row, 2).text()
            file_path = Path(file_path_str)
        elif self.files:
            file_path = self.files[0].path
        else:
            return

        if file_path.exists():
            folder = file_path.parent if file_path.is_file() else file_path
            try:
                subprocess.Popen(f'explorer /select,"{file_path}"')
            except Exception:
                try:
                    os.startfile(folder)
                except Exception:
                    pass
