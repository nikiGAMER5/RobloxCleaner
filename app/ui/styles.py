"""Modern dark mode themes and Qt stylesheets for Roblox Cleaner."""

from __future__ import annotations


THEMES = {
    "dark": {
        "name": "Dark Modern",
        "bg_main": "#0d1117",
        "bg_card": "#161b22",
        "bg_card_hover": "#21262d",
        "bg_input": "#0d1117",
        "border": "#30363d",
        "text_primary": "#f0f6fc",
        "text_secondary": "#8b949e",
        "accent": "#58a6ff",
        "accent_hover": "#79b8ff",
        "accent_pressed": "#388bfd",
        "clean_btn": "#238636",
        "clean_btn_hover": "#2ea043",
        "clean_btn_pressed": "#1a7f37",
        "danger": "#f85149",
        "warning": "#d29922",
        "warning_bg": "rgba(210, 153, 34, 0.15)",
        "card_header": "#1f242c",
    },
    "deep_black": {
        "name": "OLED Midnight",
        "bg_main": "#000000",
        "bg_card": "#0c0d0e",
        "bg_card_hover": "#16181a",
        "bg_input": "#050505",
        "border": "#22252a",
        "text_primary": "#ffffff",
        "text_secondary": "#71767b",
        "accent": "#2f81f7",
        "accent_hover": "#58a6ff",
        "accent_pressed": "#1f6feb",
        "clean_btn": "#238636",
        "clean_btn_hover": "#2ea043",
        "clean_btn_pressed": "#1a7f37",
        "danger": "#da3633",
        "warning": "#e3b341",
        "warning_bg": "rgba(227, 179, 65, 0.12)",
        "card_header": "#121417",
    },
    "cyber_blue": {
        "name": "Cyber Blue",
        "bg_main": "#0b132b",
        "bg_card": "#1c2541",
        "bg_card_hover": "#243258",
        "bg_input": "#0f1a36",
        "border": "#3a506b",
        "text_primary": "#f8f9fa",
        "text_secondary": "#8ea8c3",
        "accent": "#00f0ff",
        "accent_hover": "#4df4ff",
        "accent_pressed": "#00bcd4",
        "clean_btn": "#00e676",
        "clean_btn_hover": "#33eb91",
        "clean_btn_pressed": "#00c853",
        "danger": "#ff3860",
        "warning": "#ffd166",
        "warning_bg": "rgba(255, 209, 102, 0.15)",
        "card_header": "#17203b",
    },
}


def get_stylesheet(theme_key: str = "dark") -> str:
    """Generate the complete QSS stylesheet for the application."""
    t = THEMES.get(theme_key, THEMES["dark"])

    return f"""
    /* General Window */
    QMainWindow, QDialog {{
        background-color: {t["bg_main"]};
        color: {t["text_primary"]};
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
        font-size: 13px;
    }}

    QWidget {{
        color: {t["text_primary"]};
    }}

    /* Card Panels */
    QFrame#cardFrame {{
        background-color: {t["bg_card"]};
        border: 1px solid {t["border"]};
        border-radius: 10px;
    }}

    QFrame#statCard {{
        background-color: {t["bg_card"]};
        border: 1px solid {t["border"]};
        border-radius: 10px;
        padding: 12px;
    }}

    QFrame#warningBanner {{
        background-color: {t["warning_bg"]};
        border: 1px solid {t["warning"]};
        border-radius: 8px;
        padding: 8px 14px;
    }}

    /* Headings & Labels */
    QLabel#appTitle {{
        font-size: 20px;
        font-weight: 700;
        color: {t["text_primary"]};
    }}

    QLabel#appSubtitle {{
        font-size: 12px;
        color: {t["text_secondary"]};
    }}

    QLabel#statTitle {{
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        color: {t["text_secondary"]};
        letter-spacing: 0.5px;
    }}

    QLabel#statValue {{
        font-size: 24px;
        font-weight: 700;
        color: {t["accent"]};
    }}

    QLabel#statSub {{
        font-size: 11px;
        color: {t["text_secondary"]};
    }}

    QLabel#sectionHeader {{
        font-size: 14px;
        font-weight: 600;
        color: {t["text_primary"]};
    }}

    QLabel#statusLabel {{
        font-size: 12px;
        color: {t["text_secondary"]};
    }}

    /* Primary Scan Button */
    QPushButton#scanBtn {{
        background-color: {t["accent"]};
        color: #ffffff;
        font-weight: 600;
        font-size: 13px;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
    }}

    QPushButton#scanBtn:hover {{
        background-color: {t["accent_hover"]};
    }}

    QPushButton#scanBtn:pressed {{
        background-color: {t["accent_pressed"]};
    }}

    QPushButton#scanBtn:disabled {{
        background-color: {t["border"]};
        color: {t["text_secondary"]};
    }}

    /* Primary Clean Button */
    QPushButton#cleanBtn {{
        background-color: {t["clean_btn"]};
        color: #ffffff;
        font-weight: 700;
        font-size: 13px;
        border: none;
        border-radius: 8px;
        padding: 10px 28px;
    }}

    QPushButton#cleanBtn:hover {{
        background-color: {t["clean_btn_hover"]};
    }}

    QPushButton#cleanBtn:pressed {{
        background-color: {t["clean_btn_pressed"]};
    }}

    QPushButton#cleanBtn:disabled {{
        background-color: {t["border"]};
        color: {t["text_secondary"]};
    }}

    /* Secondary / Action Buttons */
    QPushButton#secondaryBtn {{
        background-color: {t["bg_card"]};
        color: {t["text_primary"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        font-weight: 500;
        padding: 8px 16px;
    }}

    QPushButton#secondaryBtn:hover {{
        background-color: {t["bg_card_hover"]};
        border-color: {t["accent"]};
    }}

    QPushButton#tableActionBtn {{
        background-color: {t["bg_card"]};
        color: {t["text_primary"]};
        border: 1px solid {t["border"]};
        border-radius: 6px;
        font-weight: 500;
        font-size: 11px;
        padding: 4px 10px;
        min-height: 24px;
        max-height: 26px;
    }}

    QPushButton#tableActionBtn:hover {{
        background-color: {t["bg_card_hover"]};
        border-color: {t["accent"]};
        color: #ffffff;
    }}

    QPushButton#tableActionBtn:disabled {{
        background-color: transparent;
        border-color: {t["border"]};
        color: {t["text_secondary"]};
    }}

    QPushButton#warnActionBtn {{
        background-color: {t["warning"]};
        color: #000000;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        padding: 6px 14px;
        font-size: 11px;
    }}

    QPushButton#warnActionBtn:hover {{
        background-color: #e59b00;
    }}

    QPushButton#iconBtn {{
        background-color: transparent;
        border: 1px solid {t["border"]};
        border-radius: 8px;
        color: {t["text_secondary"]};
        padding: 6px 10px;
        font-size: 14px;
    }}

    QPushButton#iconBtn:hover {{
        background-color: {t["bg_card_hover"]};
        color: {t["text_primary"]};
        border-color: {t["text_secondary"]};
    }}

    QProgressBar {{
        background-color: {t["bg_card"]};
        border: 1px solid {t["border"]};
        border-radius: 6px;
        text-align: center;
        color: {t["text_primary"]};
        font-size: 11px;
        font-weight: 600;
        height: 12px;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {t["accent"]}, stop:1 {t["clean_btn"]});
        border-radius: 5px;
    }}

    QTableWidget, QTreeWidget {{
        background-color: {t["bg_card"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        gridline-color: {t["border"]};
        color: {t["text_primary"]};
        selection-background-color: {t["bg_card_hover"]};
        selection-color: {t["text_primary"]};
        alternate-background-color: {t["bg_main"]};
    }}

    QHeaderView::section {{
        background-color: {t["card_header"]};
        color: {t["text_secondary"]};
        font-weight: 600;
        font-size: 12px;
        border: none;
        border-bottom: 1px solid {t["border"]};
        padding: 8px 12px;
    }}

    QTableWidget::item {{
        padding: 2px 10px;
        border-bottom: 1px solid {t["border"]};
    }}

    QTableWidget::item:selected {{
        background-color: {t["bg_card_hover"]};
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        border: none;
        background: {t["bg_main"]};
        width: 8px;
        margin: 0px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical {{
        background: {t["border"]};
        min-height: 20px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {t["text_secondary"]};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* Inputs, ComboBox, CheckBoxes */
    QLineEdit, QComboBox {{
        background-color: {t["bg_input"]};
        border: 1px solid {t["border"]};
        border-radius: 6px;
        color: {t["text_primary"]};
        padding: 8px 12px;
    }}

    QLineEdit:focus, QComboBox:focus {{
        border-color: {t["accent"]};
    }}

    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {t["bg_card"]};
        border: 1px solid {t["border"]};
        selection-background-color: {t["bg_card_hover"]};
        color: {t["text_primary"]};
    }}

    QCheckBox {{
        spacing: 8px;
        color: {t["text_primary"]};
        font-size: 13px;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {t["border"]};
        border-radius: 4px;
        background-color: {t["bg_input"]};
    }}

    QCheckBox::indicator:hover {{
        border-color: {t["accent"]};
    }}

    QCheckBox::indicator:checked {{
        background-color: {t["accent"]};
        border-color: {t["accent"]};
        image: none;
    }}

    /* Dropdown Menus */
    QMenu {{
        background-color: {t["bg_card"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        padding: 6px;
        color: {t["text_primary"]};
    }}

    QMenu::item {{
        padding: 7px 22px 7px 14px;
        border-radius: 5px;
        color: {t["text_primary"]};
        font-size: 12px;
    }}

    QMenu::item:selected {{
        background-color: {t["bg_card_hover"]};
        color: {t["accent"]};
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {t["border"]};
        margin: 4px 6px;
    }}
    """
