"""Progress log panel with progress bar."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QPlainTextEdit
from PySide6.QtCore import Qt


class ProgressPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(500)
        layout.addWidget(self.log_view)

    def append_log(self, text: str):
        self.log_view.appendPlainText(text)
        # Auto-scroll to bottom
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def set_progress(self, pct: int):
        self.progress_bar.setValue(pct)

    def clear(self):
        self.log_view.clear()
        self.progress_bar.setValue(0)
