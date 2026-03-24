"""Home page: URL input, quick-setting cards, progress log, Markdown preview."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFrame,
    QSplitter, QPlainTextEdit, QProgressBar,
    QTextBrowser, QApplication, QSizePolicy, QFileDialog,
)
from PySide6.QtCore import Qt, Signal

try:
    import markdown
    _HAS_MARKDOWN = True
except ImportError:
    _HAS_MARKDOWN = False

from ytb_summarizer.summarizer import PROVIDER_MODELS
from ytb_summarizer.templates import list_templates
from ytb_gui import config as cfg


class HomePage(QWidget):
    start_requested = Signal(dict)
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load_config()

    # ── Build ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 24)
        root.setSpacing(0)

        # Title
        title = QLabel("New Summary")
        title.setObjectName("page_title")
        root.addWidget(title)

        sub = QLabel("Paste a YouTube URL to generate a high-precision summary.")
        sub.setObjectName("page_subtitle")
        root.addWidget(sub)
        root.addSpacing(24)

        # ── URL row ──────────────────────────────────────────────────────────
        url_row = QHBoxLayout()
        url_row.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setObjectName("url_input")
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...  或  https://www.bilibili.com/video/BV...")
        self.url_input.setMinimumHeight(50)
        self.url_input.returnPressed.connect(self._on_start)
        url_row.addWidget(self.url_input, stretch=1)

        self.summarize_btn = QPushButton("Summarize")
        self.summarize_btn.setObjectName("summarize_btn")
        self.summarize_btn.setFixedWidth(130)
        self.summarize_btn.setMinimumHeight(50)
        self.summarize_btn.clicked.connect(self._on_start)
        url_row.addWidget(self.summarize_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setFixedWidth(75)
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_requested)
        url_row.addWidget(self.stop_btn)

        root.addLayout(url_row)
        root.addSpacing(16)

        # ── Quick settings cards ──────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        # Provider + Model card
        provider_card, provider_inner = _make_card()
        _card_label(provider_inner, "MODEL")
        pm_row = QHBoxLayout()
        pm_row.setSpacing(6)
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["anthropic", "openai", "deepseek", "custom"])
        self.provider_combo.setFixedWidth(110)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        pm_row.addWidget(self.provider_combo)
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        pm_row.addWidget(self.model_combo)
        provider_inner.addLayout(pm_row)
        cards_row.addWidget(provider_card)

        # Template card
        tmpl_card, tmpl_inner = _make_card()
        _card_label(tmpl_inner, "PROMPT PROFILE")
        self.template_combo = QComboBox()
        tmpl_inner.addWidget(self.template_combo)
        cards_row.addWidget(tmpl_card)

        # Language card
        lang_card, lang_inner = _make_card()
        _card_label(lang_inner, "TRANSCRIPT LANG")
        self.lang_combo = QComboBox()
        for code, label in [
            ("en", "en · English"), ("zh", "zh · 中文"),
            ("zh-Hans", "zh-Hans · 简体"), ("ja", "ja · 日本語"),
            ("ko", "ko · 한국어"), ("fr", "fr · Français"),
            ("de", "de · Deutsch"), ("es", "es · Español"),
        ]:
            self.lang_combo.addItem(label, code)
        lang_inner.addWidget(self.lang_combo)
        cards_row.addWidget(lang_card)

        root.addLayout(cards_row)
        root.addSpacing(10)

        # ── Output directory row ──────────────────────────────────────────────
        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        out_lbl = QLabel("Save to:")
        out_lbl.setObjectName("card_label_small")
        out_lbl.setFixedWidth(60)
        out_row.addWidget(out_lbl)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Output directory…")
        out_row.addWidget(self.output_edit, stretch=1)
        browse_out_btn = QPushButton("Browse…")
        browse_out_btn.setFixedWidth(80)
        browse_out_btn.clicked.connect(self._browse_output)
        out_row.addWidget(browse_out_btn)
        root.addLayout(out_row)
        root.addSpacing(16)

        # ── Work area (progress + preview) ─────────────────────────────────
        self.work_area = QSplitter(Qt.Orientation.Horizontal)

        # Left: progress
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        left_layout.addWidget(self.progress_bar)

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("log_view")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(500)
        left_layout.addWidget(self.log_view)
        self.work_area.addWidget(left_widget)

        # Right: preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        toolbar = QWidget()
        toolbar.setObjectName("preview_toolbar")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.setSpacing(6)

        self.open_btn = QPushButton("Open File")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open_file)
        tb_layout.addWidget(self.open_btn)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self._copy_all)
        tb_layout.addWidget(self.copy_btn)
        tb_layout.addStretch()
        right_layout.addWidget(toolbar)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        right_layout.addWidget(self.preview)
        self.work_area.addWidget(right_widget)

        self.work_area.setSizes([420, 580])
        root.addWidget(self.work_area, stretch=1)

        self._current_content = ""
        self._current_path: str | None = None

    # ── Config ───────────────────────────────────────────────────────────────

    def _load_config(self):
        conf = cfg.load()

        provider = conf.get("provider", "anthropic")
        idx = self.provider_combo.findText(provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        self._on_provider_changed(provider)

        model = conf.get("model", "")
        midx = self.model_combo.findText(model)
        if midx >= 0:
            self.model_combo.setCurrentIndex(midx)
        elif model:
            self.model_combo.setCurrentText(model)

        self._refresh_templates()
        tmpl = conf.get("template", "default")
        tidx = self.template_combo.findText(tmpl)
        if tidx >= 0:
            self.template_combo.setCurrentIndex(tidx)

        self.output_edit.setText(conf.get("output_dir", str(cfg.summaries_dir())))

        lang = conf.get("transcript_lang", "en")
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == lang:
                self.lang_combo.setCurrentIndex(i)
                break

    def _on_provider_changed(self, provider: str):
        models = PROVIDER_MODELS.get(provider, [])
        self.model_combo.clear()
        self.model_combo.addItems(models)

    def refresh_templates(self):
        current = self.template_combo.currentText()
        self._refresh_templates()
        idx = self.template_combo.findText(current)
        if idx >= 0:
            self.template_combo.setCurrentIndex(idx)

    def _refresh_templates(self):
        self.template_combo.clear()
        self.template_combo.addItems(list_templates(custom_dir=cfg.templates_dir()))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_start(self):
        url = self.url_input.text().strip()
        if not url:
            return

        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText().strip()
        conf = cfg.load()
        api_key = conf.get("api_keys", {}).get(provider, "")
        base_url = conf.get("base_url", "")

        provider_config = {"provider": provider, "api_key": api_key, "model": model}
        if base_url:
            provider_config["base_url"] = base_url

        output_dir = self.output_edit.text().strip() or str(cfg.summaries_dir())
        transcript_lang = self.lang_combo.currentData() or "en"
        template = self.template_combo.currentText()

        # Save quick settings
        conf["provider"] = provider
        conf["model"] = model
        conf["template"] = template
        conf["transcript_lang"] = transcript_lang
        conf["output_dir"] = output_dir
        cfg.save(conf)

        self.start_requested.emit({
            "url": url,
            "provider_config": provider_config,
            "template": template,
            "output_dir": output_dir,
            "transcript_lang": transcript_lang,
        })

    # ── Progress slots ────────────────────────────────────────────────────────

    def append_log(self, text: str):
        self.log_view.appendPlainText(text)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def set_progress(self, pct: int):
        self.progress_bar.setValue(pct)

    def clear_work_area(self):
        self.log_view.clear()
        self.progress_bar.setValue(0)
        self.preview.clear()
        self.open_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)
        self._current_content = ""
        self._current_path = None

    def show_result(self, content: str, path: str):
        self._current_content = content
        self._current_path = path
        if _HAS_MARKDOWN:
            html = markdown.markdown(
                content,
                extensions=["tables", "fenced_code", "nl2br"],
            )
            styled = f"""<html><head><style>
body{{font-family:inherit;font-size:13px;background:#06122d;color:#dee5ff;padding:8px;line-height:1.6}}
h1{{color:#e2e2e2;border-bottom:1px solid #2b4680;padding-bottom:6px}}
h2{{color:#c6c6c7;border-bottom:1px solid rgba(43,70,128,0.3);padding-bottom:4px}}
h3{{color:#b0b8d0}}
code{{background:#031d4b;color:#dee5ff;padding:2px 5px;border-radius:3px;font-family:monospace}}
pre{{background:#031d4b;padding:12px;border-radius:6px;overflow-x:auto}}
blockquote{{border-left:3px solid #5b74b1;padding-left:12px;color:#909fb4;margin:0}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #2b4680;padding:7px 12px}}
th{{background:#05183c;color:#909fb4}}
a{{color:#91aaeb}}
</style></head><body>{html}</body></html>"""
            self.preview.setHtml(styled)
        else:
            self.preview.setPlainText(content)
        self.open_btn.setEnabled(True)
        self.copy_btn.setEnabled(True)

    def set_running(self, running: bool):
        self.summarize_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.url_input.setEnabled(not running)

    # ── Preview actions ───────────────────────────────────────────────────────

    def _open_file(self):
        if not self._current_path:
            return
        p = Path(self._current_path)
        if not p.exists():
            return
        if sys.platform == "win32":
            os.startfile(str(p))          # opens with default app (Notepad / VS Code / etc.)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p)])

    def _browse_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Directory",
                                             self.output_edit.text())
        if d:
            self.output_edit.setText(d)

    def _copy_all(self):
        QApplication.clipboard().setText(self._current_content)

    # ── Public helpers ────────────────────────────────────────────────────────

    def get_url(self) -> str:
        return self.url_input.text().strip()

    def set_url(self, url: str):
        self.url_input.setText(url)


# ── Card helpers ──────────────────────────────────────────────────────────────

def _make_card() -> tuple[QFrame, QVBoxLayout]:
    card = QFrame()
    card.setObjectName("settings_card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 10, 14, 10)
    layout.setSpacing(4)
    return card, layout


def _card_label(layout: QVBoxLayout, text: str):
    lbl = QLabel(text)
    lbl.setObjectName("card_label_small")
    layout.addWidget(lbl)
