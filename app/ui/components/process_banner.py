"""Warning banner component displayed when Roblox is actively running."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QWidget,
)

from app.cleaner.process_manager import RobloxProcessManager
from app.utils.i18n import tr


class ProcessBanner(QFrame):
    """Warning banner shown when a running Roblox instance is detected."""

    roblox_status_changed = Signal(bool)

    def __init__(self, lang: str = "en", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("warningBanner")
        self.lang = lang
        self.process_manager = RobloxProcessManager()
        self._is_running = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        self.msg_label = QLabel(tr("roblox_running_banner", self.lang))
        self.msg_label.setStyleSheet("color: #d29922; font-size: 12px;")
        layout.addWidget(self.msg_label)

        layout.addStretch()

        self.btn_close_roblox = QPushButton(tr("btn_close_roblox", self.lang))
        self.btn_close_roblox.setObjectName("warnActionBtn")
        self.btn_close_roblox.clicked.connect(self._handle_close_request)
        layout.addWidget(self.btn_close_roblox)

        self.hide()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_status)
        self.timer.start(2500)

    def update_language(self, lang: str) -> None:
        """Update banner text according to language."""
        self.lang = lang
        self.msg_label.setText(tr("roblox_running_banner", self.lang))
        self.btn_close_roblox.setText(tr("btn_close_roblox", self.lang))

    def check_status(self) -> bool:
        """Query if Roblox is running and update banner visibility accordingly."""
        running = self.process_manager.is_roblox_running()
        if running != self._is_running:
            self._is_running = running
            self.setVisible(running)
            self.roblox_status_changed.emit(running)
        return running

    def _handle_close_request(self) -> None:
        """Prompt user confirmation and terminate Roblox."""
        is_en = self.lang == "en"
        reply = QMessageBox.question(
            self,
            "Terminate Roblox" if is_en else "Roblox beenden",
            "Do you really want to close running Roblox processes now?\n\nAny unsaved in-game progress could be lost."
            if is_en
            else "Möchtest du laufende Roblox-Prozesse jetzt wirklich beenden?\n\nNicht gespeicherte Sitzungsdaten im Spiel könnten verloren gehen.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            terminated, failed, msg = self.process_manager.terminate_roblox()
            title = "Success" if is_en else "Erfolg"
            warn_title = "Notice" if is_en else "Hinweis"
            if terminated > 0:
                QMessageBox.information(self, title, msg)
            else:
                QMessageBox.warning(self, warn_title, msg)
            self.check_status()
