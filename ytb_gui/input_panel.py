"""Input panel: URL, provider, model, API key, template, output dir."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFileDialog, QSizePolicy,
)
from PySide6.QtCore import Signal

from ytb_summarizer.summarizer import PROVIDER_MODELS
from ytb_summarizer.templates import list_templates
from ytb_gui import config as cfg


TRANSCRIPT_LANGS = [
    ("en", "en - English"),
    ("zh", "zh - 中文"),
    ("zh-Hans", "zh-Hans - 简体中文"),
    ("ja", "ja - 日本語"),
    ("ko", "ko - 한국어"),
    ("fr", "fr - Français"),
    ("de", "de - Deutsch"),
    ("es", "es - Español"),
    ("ru", "ru - Русский"),
    ("ar", "ar - العربية"),
]


class InputPanel(QWidget):
    start_requested = Signal(dict)   # emits provider_config + settings dict
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._conf = cfg.load()
        self._build_ui()
        self._load_config()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(6)

        # ── URL row ──
        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("YouTube URL:"))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://youtube.com/watch?v=... 或播放列表链接")
        url_row.addWidget(self.url_edit)
        paste_btn = QPushButton("粘贴")
        paste_btn.setFixedWidth(50)
        paste_btn.clicked.connect(self._paste_url)
        url_row.addWidget(paste_btn)
        root.addLayout(url_row)

        # ── Provider + Model row ──
        pm_row = QHBoxLayout()
        pm_row.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["anthropic", "openai", "deepseek", "custom"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        self.provider_combo.setFixedWidth(130)
        pm_row.addWidget(self.provider_combo)

        pm_row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setMinimumWidth(220)
        pm_row.addWidget(self.model_combo)
        pm_row.addStretch()
        root.addLayout(pm_row)

        # ── API Key row ──
        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("API Key:"))
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText("sk-...")
        key_row.addWidget(self.key_edit)
        show_btn = QPushButton("显示")
        show_btn.setFixedWidth(50)
        show_btn.setCheckable(True)
        show_btn.toggled.connect(self._toggle_key_visibility)
        key_row.addWidget(show_btn)
        save_key_btn = QPushButton("保存")
        save_key_btn.setFixedWidth(50)
        save_key_btn.clicked.connect(self._save_key)
        key_row.addWidget(save_key_btn)
        root.addLayout(key_row)

        # ── Base URL row (custom/deepseek) ──
        bu_row = QHBoxLayout()
        self._bu_label = QLabel("Base URL:")
        bu_row.addWidget(self._bu_label)
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.example.com")
        bu_row.addWidget(self.base_url_edit)
        self._bu_row_widget = QWidget()
        self._bu_row_widget.setLayout(bu_row)
        root.addWidget(self._bu_row_widget)

        # ── Template + Output row ──
        to_row = QHBoxLayout()
        to_row.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        self._refresh_templates()
        self.template_combo.setFixedWidth(150)
        to_row.addWidget(self.template_combo)

        to_row.addWidget(QLabel("Output:"))
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("./summaries")
        to_row.addWidget(self.output_edit)
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._browse_output)
        to_row.addWidget(browse_btn)
        root.addLayout(to_row)

        # ── Language row ──
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("字幕语言:"))
        self.trans_lang_combo = QComboBox()
        for code, label in TRANSCRIPT_LANGS:
            self.trans_lang_combo.addItem(label, code)
        self.trans_lang_combo.setFixedWidth(180)
        lang_row.addWidget(self.trans_lang_combo)
        lang_row.addStretch()
        root.addLayout(lang_row)

        # ── Action buttons ──
        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("开始总结")
        self.start_btn.setMinimumHeight(36)
        self.start_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.start_btn.clicked.connect(self._on_start)
        btn_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedWidth(70)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_requested)
        btn_row.addWidget(self.stop_btn)
        root.addLayout(btn_row)

        # Init provider UI
        self._on_provider_changed(self.provider_combo.currentText())

    def _load_config(self):
        conf = self._conf
        provider = conf.get("provider", "anthropic")
        idx = self.provider_combo.findText(provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)

        model = conf.get("model", "")
        if model:
            midx = self.model_combo.findText(model)
            if midx >= 0:
                self.model_combo.setCurrentIndex(midx)
            else:
                self.model_combo.setCurrentText(model)

        api_keys = conf.get("api_keys", {})
        self.key_edit.setText(api_keys.get(provider, ""))
        self.base_url_edit.setText(conf.get("base_url", ""))
        self.output_edit.setText(conf.get("output_dir", str(cfg.summaries_dir())))

        tmpl = conf.get("template", "default")
        tidx = self.template_combo.findText(tmpl)
        if tidx >= 0:
            self.template_combo.setCurrentIndex(tidx)

        lang = conf.get("transcript_lang", "en")
        for i in range(self.trans_lang_combo.count()):
            if self.trans_lang_combo.itemData(i) == lang:
                self.trans_lang_combo.setCurrentIndex(i)
                break

    def _on_provider_changed(self, provider: str):
        models = PROVIDER_MODELS.get(provider, [])
        self.model_combo.clear()
        self.model_combo.addItems(models)
        # Show/hide base URL
        show_bu = provider in ("deepseek", "custom")
        self._bu_row_widget.setVisible(show_bu)
        if provider == "deepseek":
            self.base_url_edit.setText("https://api.deepseek.com")
        # Load saved API key for this provider
        api_keys = self._conf.get("api_keys", {})
        self.key_edit.setText(api_keys.get(provider, ""))

    def _toggle_key_visibility(self, checked: bool):
        if checked:
            self.key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def _save_key(self):
        conf = cfg.load()
        provider = self.provider_combo.currentText()
        if "api_keys" not in conf:
            conf["api_keys"] = {}
        conf["api_keys"][provider] = self.key_edit.text()
        cfg.save(conf)
        self._conf = conf

    def _paste_url(self):
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        self.url_edit.setText(clipboard.text())

    def _browse_output(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_edit.setText(directory)

    def _refresh_templates(self):
        self.template_combo.clear()
        templates = list_templates(custom_dir=cfg.templates_dir())
        self.template_combo.addItems(templates)

    def refresh_templates(self):
        current = self.template_combo.currentText()
        self._refresh_templates()
        idx = self.template_combo.findText(current)
        if idx >= 0:
            self.template_combo.setCurrentIndex(idx)

    def _on_start(self):
        url = self.url_edit.text().strip()
        if not url:
            return

        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText().strip()
        api_key = self.key_edit.text().strip()
        base_url = self.base_url_edit.text().strip()

        provider_config = {
            "provider": provider,
            "api_key": api_key,
            "model": model,
        }
        if base_url:
            provider_config["base_url"] = base_url

        settings = {
            "url": url,
            "provider_config": provider_config,
            "template": self.template_combo.currentText(),
            "output_dir": self.output_edit.text().strip() or str(cfg.summaries_dir()),
            "transcript_lang": self.trans_lang_combo.currentData() or "en",
        }

        # Save current settings
        conf = cfg.load()
        conf["provider"] = provider
        conf["model"] = model
        conf["template"] = settings["template"]
        conf["output_dir"] = settings["output_dir"]
        conf["transcript_lang"] = settings["transcript_lang"]
        conf["base_url"] = base_url
        cfg.save(conf)

        self.start_requested.emit(settings)

    def set_running(self, running: bool):
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
