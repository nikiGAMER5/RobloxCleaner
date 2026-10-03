"""Reusable modern statistic card component."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class StatCard(QFrame):
    """Card widget displaying a metric with title, main value and auxiliary text."""

    def __init__(
        self,
        title: str,
        initial_value: str = "0",
        initial_sub: str = "-",
        accent_color: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("statCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("statTitle")

        self.value_label = QLabel(initial_value)
        self.value_label.setObjectName("statValue")
        if accent_color:
            self.value_label.setStyleSheet(f"color: {accent_color};")

        self.sub_label = QLabel(initial_sub)
        self.sub_label.setObjectName("statSub")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.sub_label)

    def set_value(self, value: str, sub_text: str | None = None) -> None:
        """Update card value and optional sub text."""
        self.value_label.setText(value)
        if sub_text is not None:
            self.sub_label.setText(sub_text)

    def set_title(self, title: str) -> None:
        """Update card title."""
        self.title_label.setText(title.upper())
