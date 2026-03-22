"""Markdown preview panel using QTextBrowser."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

try:
    import markdown
    _HAS_MARKDOWN = True
except ImportError:
    _HAS_MARKDOWN = False


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path: str | None = None
        self._current_content: str = ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        self.open_btn = QPushButton("打开文件")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open_file)
        toolbar.addWidget(self.open_btn)

        self.copy_btn = QPushButton("复制全文")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self._copy_all)
        toolbar.addWidget(self.copy_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        layout.addWidget(self.text_browser)

    def show_content(self, markdown_text: str, file_path: str | None = None):
        self._current_content = markdown_text
        self._current_path = file_path

        if _HAS_MARKDOWN:
            html = markdown.markdown(
                markdown_text,
                extensions=["tables", "fenced_code", "nl2br"],
            )
            # Basic styling
            styled = f"""
<html><head><style>
body {{ font-family: -apple-system, Arial, sans-serif; font-size: 14px; padding: 8px; }}
h1 {{ border-bottom: 2px solid #eee; }}
h2 {{ border-bottom: 1px solid #eee; }}
code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; font-family: monospace; }}
pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
blockquote {{ border-left: 4px solid #ddd; padding-left: 10px; color: #666; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 6px 10px; }}
th {{ background: #f4f4f4; }}
</style></head><body>{html}</body></html>"""
            self.text_browser.setHtml(styled)
        else:
            self.text_browser.setPlainText(markdown_text)

        self.copy_btn.setEnabled(True)
        self.open_btn.setEnabled(file_path is not None)

    def clear(self):
        self.text_browser.clear()
        self._current_content = ""
        self._current_path = None
        self.copy_btn.setEnabled(False)
        self.open_btn.setEnabled(False)

    def _open_file(self):
        if not self._current_path:
            return
        path = Path(self._current_path)
        if not path.exists():
            return
        if sys.platform == "win32":
            subprocess.Popen(["explorer", str(path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def _copy_all(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._current_content)
