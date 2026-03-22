"""Entry point for the YouTube Summarizer application."""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ytb_gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Summarizer")
    app.setOrganizationName("ytb-summarizer")

    # Enable high DPI support
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
