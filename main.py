"""Entry point for the YouTube Summarizer application."""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase

from ytb_gui.main_window import MainWindow
from ytb_gui.style import DARK_THEME


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("YT Summarizer")
    app.setOrganizationName("ytb-summarizer")

    # Apply dark theme
    app.setStyleSheet(DARK_THEME)

    # Prefer a CJK-capable font so Chinese characters render correctly
    cjk_candidates = [
        "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC",
        "WenQuanYi Micro Hei", "Source Han Sans SC",
    ]
    available = set(QFontDatabase.families())
    chosen = next((f for f in cjk_candidates if f in available), None)
    if chosen:
        app.setFont(QFont(chosen, 10))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
