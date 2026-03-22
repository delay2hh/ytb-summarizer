"""Main application window with tab layout."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QStatusBar, QMessageBox,
)
from PySide6.QtCore import Qt

from ytb_gui.input_panel import InputPanel
from ytb_gui.progress_panel import ProgressPanel
from ytb_gui.preview_panel import PreviewPanel
from ytb_gui.history_panel import HistoryPanel
from ytb_gui.template_editor import TemplateEditor
from ytb_gui.worker import SummarizeWorker
from ytb_gui import config as cfg


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Summarizer")
        self.resize(1100, 750)
        self._worker: SummarizeWorker | None = None
        self._last_url: str = ""
        self._last_provider: str = ""
        self._last_template: str = ""
        self._last_output_path: str = ""
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ── Input panel (top) ──
        self.input_panel = InputPanel()
        self.input_panel.start_requested.connect(self._on_start)
        self.input_panel.stop_requested.connect(self._on_stop)
        root.addWidget(self.input_panel)

        # ── Middle: progress + preview splitter ──
        mid_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.progress_panel = ProgressPanel()
        mid_splitter.addWidget(self.progress_panel)

        self.preview_panel = PreviewPanel()
        mid_splitter.addWidget(self.preview_panel)
        mid_splitter.setSizes([400, 600])
        root.addWidget(mid_splitter, stretch=1)

        # ── Bottom tabs ──
        self.tabs = QTabWidget()

        self.history_panel = HistoryPanel()
        self.history_panel.rerun_requested.connect(self._on_rerun)
        self.tabs.addTab(self.history_panel, "历史记录")

        self.template_editor = TemplateEditor()
        self.template_editor.templates_changed.connect(self.input_panel.refresh_templates)
        self.tabs.addTab(self.template_editor, "模板编辑器")

        self.tabs.setMaximumHeight(280)
        root.addWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _on_start(self, settings: dict):
        if self._worker and self._worker.isRunning():
            return

        url = settings["url"]
        provider_config = settings["provider_config"]

        if not provider_config.get("api_key"):
            QMessageBox.warning(self, "缺少 API Key", "请输入 API Key 后再开始。")
            return

        self._last_url = url
        self._last_provider = provider_config["provider"]
        self._last_template = settings["template"]

        self.progress_panel.clear()
        self.preview_panel.clear()
        self.input_panel.set_running(True)
        self.status_bar.showMessage("正在处理...")

        self._worker = SummarizeWorker(
            url=url,
            provider_config=provider_config,
            template_name=settings["template"],
            output_dir=settings["output_dir"],
            transcript_lang=settings["transcript_lang"],
        )
        self._worker.progress.connect(self.progress_panel.append_log)
        self._worker.progress_pct.connect(self.progress_panel.set_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_stop(self):
        if self._worker:
            self._worker.cancel()
            self._worker.wait(3000)
            self.input_panel.set_running(False)
            self.status_bar.showMessage("已停止")

    def _on_finished(self, content: str, output_path: str):
        self._last_output_path = output_path
        self.preview_panel.show_content(content, output_path)
        self.input_panel.set_running(False)
        self.status_bar.showMessage(f"完成 → {output_path}")

        # Extract title from content (first H1 line)
        title = ""
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        self.history_panel.add_entry(
            url=self._last_url,
            title=title or self._last_url,
            template=self._last_template,
            provider=self._last_provider,
            output_path=output_path,
        )

    def _on_error(self, msg: str):
        self.input_panel.set_running(False)
        self.progress_panel.append_log(f"❌ 错误: {msg}")
        self.status_bar.showMessage(f"错误: {msg}")
        QMessageBox.critical(self, "处理失败", msg)

    def _on_rerun(self, url: str):
        self.input_panel.url_edit.setText(url)
        # Switch focus to input
        self.tabs.setCurrentIndex(0)
