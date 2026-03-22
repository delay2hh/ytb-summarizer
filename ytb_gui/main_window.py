"""Main window: left sidebar + stacked pages."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QStatusBar,
    QMessageBox, QSizePolicy, QFrame,
)
from PySide6.QtCore import Qt

from ytb_gui.home_page import HomePage
from ytb_gui.history_panel import HistoryPanel
from ytb_gui.settings_page import SettingsPage
from ytb_gui.worker import SummarizeWorker
from ytb_gui import config as cfg


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT Summarizer")
        self.resize(1260, 820)
        self._worker: SummarizeWorker | None = None
        self._last_url = ""
        self._last_provider = ""
        self._last_template = ""

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        # Pages
        self._stack = QStackedWidget()
        self._home = HomePage()
        self._history = HistoryPanel()
        self._settings = SettingsPage()

        self._stack.addWidget(self._home)       # 0
        self._stack.addWidget(self._history)    # 1
        self._stack.addWidget(self._settings)   # 2
        root.addWidget(self._stack, stretch=1)

        # Connect signals
        self._home.start_requested.connect(self._on_start)
        self._home.stop_requested.connect(self._on_stop)
        self._history.rerun_requested.connect(self._on_rerun)
        self._settings.templates_changed.connect(self._home.refresh_templates)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready  ·  YT Summarizer")

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 20, 14, 16)
        layout.setSpacing(2)

        # Logo
        logo_row = QHBoxLayout()
        icon_lbl = QLabel("YT")
        icon_lbl.setObjectName("logo_icon")
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_row.addWidget(icon_lbl)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        app_title = QLabel("YT Summarizer")
        app_title.setObjectName("app_title")
        titles.addWidget(app_title)
        pro_lbl = QLabel("PRO EDITION")
        pro_lbl.setObjectName("app_subtitle")
        titles.addWidget(pro_lbl)
        logo_row.addLayout(titles)
        logo_row.addStretch()
        layout.addLayout(logo_row)
        layout.addSpacing(24)

        # Divider
        div = QFrame()
        div.setObjectName("divider")
        layout.addWidget(div)
        layout.addSpacing(12)

        # Nav buttons
        self._nav_btns: list[QPushButton] = []
        nav_items = [
            ("Home", 0),
            ("History", 1),
            ("Settings", 2),
        ]
        for label, page_idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setChecked(page_idx == 0)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setMinimumHeight(38)
            btn.clicked.connect(lambda _, i=page_idx: self._switch_page(i))
            layout.addWidget(btn)
            self._nav_btns.append(btn)

        layout.addStretch()

        # Footer: status indicator
        div2 = QFrame()
        div2.setObjectName("divider")
        layout.addWidget(div2)
        layout.addSpacing(10)

        status_row = QHBoxLayout()
        dot = QLabel("●")
        dot.setObjectName("status_dot_ok")
        status_row.addWidget(dot)
        status_lbl = QLabel("MCP CONNECTED")
        status_lbl.setObjectName("footer_label")
        status_row.addWidget(status_lbl)
        status_row.addStretch()
        layout.addLayout(status_row)

        return sidebar

    def _switch_page(self, index: int):
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == index)
        if index == 1:
            self._history.refresh()

    # ── Worker lifecycle ──────────────────────────────────────────────────────

    def _on_start(self, settings: dict):
        if self._worker and self._worker.isRunning():
            return

        provider_config = settings["provider_config"]
        if not provider_config.get("api_key"):
            QMessageBox.warning(
                self, "API Key Missing",
                f"No API key saved for '{provider_config['provider']}'.\n"
                "Go to Settings → API & Models to add one."
            )
            self._switch_page(2)
            return

        self._last_url = settings["url"]
        self._last_provider = provider_config["provider"]
        self._last_template = settings["template"]

        self._home.clear_work_area()
        self._home.set_running(True)
        self._status.showMessage("Processing…")

        self._worker = SummarizeWorker(
            url=settings["url"],
            provider_config=provider_config,
            template_name=settings["template"],
            output_dir=settings["output_dir"],
            transcript_lang=settings["transcript_lang"],
        )
        self._worker.progress.connect(self._home.append_log)
        self._worker.progress_pct.connect(self._home.set_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_stop(self):
        if self._worker:
            self._worker.cancel()
            self._worker.wait(3000)
        self._home.set_running(False)
        self._status.showMessage("Stopped")

    def _on_finished(self, content: str, output_path: str):
        self._home.show_result(content, output_path)
        self._home.set_progress(100)
        self._home.set_running(False)
        self._status.showMessage(f"Done  ·  {output_path}")

        # Extract title from first H1 line
        title = next(
            (ln[2:].strip() for ln in content.splitlines() if ln.startswith("# ")),
            self._last_url,
        )
        self._history.add_entry(
            url=self._last_url,
            title=title,
            template=self._last_template,
            provider=self._last_provider,
            output_path=output_path,
        )

    def _on_error(self, msg: str):
        self._home.set_running(False)
        self._home.append_log(f"\n❌ Error: {msg}")
        self._status.showMessage(f"Error: {msg}")
        QMessageBox.critical(self, "Processing Failed", msg)

    def _on_rerun(self, url: str):
        self._home.set_url(url)
        self._switch_page(0)
