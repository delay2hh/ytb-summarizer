"""Settings page: API keys + base URL + output dir + template editor."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFrame,
    QFileDialog, QTabWidget, QSplitter, QListWidget,
    QPlainTextEdit, QInputDialog, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

import yaml

from ytb_summarizer.summarizer import PROVIDER_MODELS, PROVIDER_NEEDS_BASE_URL
from ytb_summarizer.templates import BUILTIN_TEMPLATES, list_templates, get_template
from ytb_gui import config as cfg


class SettingsPage(QWidget):
    templates_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 24)
        root.setSpacing(0)

        title = QLabel("Settings")
        title.setObjectName("page_title")
        root.addWidget(title)
        sub = QLabel("Configure API keys, output directory, and prompt templates.")
        sub.setObjectName("page_subtitle")
        root.addWidget(sub)
        root.addSpacing(24)

        tabs = QTabWidget()
        tabs.addTab(self._build_api_tab(), "API & Models")
        tabs.addTab(self._build_template_tab(), "Prompt Templates")
        root.addWidget(tabs, stretch=1)

    # ── API tab ───────────────────────────────────────────────────────────────

    def _build_api_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(16)

        # Provider selector
        row = QHBoxLayout()
        row.addWidget(_label("Provider"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["anthropic", "openai", "deepseek", "custom"])
        self.provider_combo.setFixedWidth(160)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        row.addWidget(self.provider_combo)
        row.addStretch()
        layout.addLayout(row)

        # API Key
        row2 = QHBoxLayout()
        row2.addWidget(_label("API Key"))
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText("sk-…")
        row2.addWidget(self.key_edit)
        show_btn = QPushButton("Show")
        show_btn.setCheckable(True)
        show_btn.setFixedWidth(60)
        show_btn.toggled.connect(
            lambda on: self.key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        row2.addWidget(show_btn)
        save_key_btn = QPushButton("Save Key")
        save_key_btn.setFixedWidth(80)
        save_key_btn.clicked.connect(self._save_key)
        row2.addWidget(save_key_btn)
        layout.addLayout(row2)

        # Base URL (custom / deepseek)
        self.bu_row_widget = QWidget()
        bu_row = QHBoxLayout(self.bu_row_widget)
        bu_row.setContentsMargins(0, 0, 0, 0)
        bu_row.addWidget(_label("Base URL"))
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.example.com")
        bu_row.addWidget(self.base_url_edit)
        save_bu_btn = QPushButton("Save")
        save_bu_btn.setFixedWidth(60)
        save_bu_btn.clicked.connect(self._save_base_url)
        bu_row.addWidget(save_bu_btn)
        layout.addWidget(self.bu_row_widget)

        # Output directory
        row3 = QHBoxLayout()
        row3.addWidget(_label("Output Dir"))
        self.output_edit = QLineEdit()
        row3.addWidget(self.output_edit)
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_output)
        row3.addWidget(browse_btn)
        save_out_btn = QPushButton("Save")
        save_out_btn.setFixedWidth(60)
        save_out_btn.clicked.connect(self._save_output)
        row3.addWidget(save_out_btn)
        layout.addLayout(row3)

        layout.addStretch()
        return w

    # ── Template tab ──────────────────────────────────────────────────────────

    def _build_template_tab(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(12)

        # Left: list + buttons
        left = QWidget()
        left.setFixedWidth(200)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        left_layout.addWidget(_label("Templates"))
        self.tmpl_list = QListWidget()
        self.tmpl_list.currentRowChanged.connect(self._on_tmpl_select)
        left_layout.addWidget(self.tmpl_list)

        btn_grid = QHBoxLayout()
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self._new_template)
        btn_grid.addWidget(new_btn)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_template)
        btn_grid.addWidget(save_btn)
        left_layout.addLayout(btn_grid)

        btn_grid2 = QHBoxLayout()
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self._delete_template)
        btn_grid2.addWidget(del_btn)
        rst_btn = QPushButton("Reset")
        rst_btn.clicked.connect(self._reset_template)
        btn_grid2.addWidget(rst_btn)
        left_layout.addLayout(btn_grid2)
        layout.addWidget(left)

        # Right: editor
        self.tmpl_editor = QPlainTextEdit()
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.tmpl_editor.setFont(font)
        layout.addWidget(self.tmpl_editor, stretch=1)

        self._refresh_tmpl_list()
        return w

    # ── Load / save ───────────────────────────────────────────────────────────

    def _load(self):
        conf = cfg.load()
        provider = conf.get("provider", "anthropic")
        idx = self.provider_combo.findText(provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        keys = conf.get("api_keys", {})
        self.key_edit.setText(keys.get(provider, ""))
        self.base_url_edit.setText(conf.get("base_url", ""))
        self.output_edit.setText(conf.get("output_dir", str(cfg.summaries_dir())))
        self._on_provider_changed(provider)

    def _on_provider_changed(self, provider: str):
        conf = cfg.load()
        self.key_edit.setText(conf.get("api_keys", {}).get(provider, ""))
        show_bu = provider in PROVIDER_NEEDS_BASE_URL
        self.bu_row_widget.setVisible(show_bu)
        if provider == "deepseek" and not self.base_url_edit.text():
            self.base_url_edit.setText("https://api.deepseek.com")

    def _save_key(self):
        conf = cfg.load()
        provider = self.provider_combo.currentText()
        conf.setdefault("api_keys", {})[provider] = self.key_edit.text()
        cfg.save(conf)

    def _save_base_url(self):
        conf = cfg.load()
        conf["base_url"] = self.base_url_edit.text().strip()
        cfg.save(conf)

    def _save_output(self):
        conf = cfg.load()
        conf["output_dir"] = self.output_edit.text().strip()
        cfg.save(conf)

    def _browse_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if d:
            self.output_edit.setText(d)

    # ── Template actions ──────────────────────────────────────────────────────

    def _refresh_tmpl_list(self):
        self.tmpl_list.clear()
        for name in list_templates(custom_dir=cfg.templates_dir()):
            self.tmpl_list.addItem(name)

    def _on_tmpl_select(self, row: int):
        if row < 0:
            return
        name = self.tmpl_list.item(row).text()
        try:
            tmpl = get_template(name, custom_dir=cfg.templates_dir())
            self.tmpl_editor.setPlainText(
                yaml.dump(tmpl, allow_unicode=True, default_flow_style=False)
            )
        except Exception as e:
            self.tmpl_editor.setPlainText(f"# Error: {e}")

    def _new_template(self):
        name, ok = QInputDialog.getText(self, "New Template", "Template name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        d = cfg.templates_dir()
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{name}.yaml"
        tmpl = {"name": name, "description": "Custom template",
                "prompt": "Please summarize:\n\nTitle: {title}\n\n{transcript}"}
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(tmpl, f, allow_unicode=True, default_flow_style=False)
        self._refresh_tmpl_list()
        self.templates_changed.emit()
        for i in range(self.tmpl_list.count()):
            if self.tmpl_list.item(i).text() == name:
                self.tmpl_list.setCurrentRow(i)
                break

    def _save_template(self):
        row = self.tmpl_list.currentRow()
        if row < 0:
            return
        name = self.tmpl_list.item(row).text()
        content = self.tmpl_editor.toPlainText()
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            QMessageBox.critical(self, "YAML Error", str(e))
            return
        d = cfg.templates_dir()
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"{name}.yaml", "w", encoding="utf-8") as f:
            f.write(content)
        self.templates_changed.emit()

    def _delete_template(self):
        row = self.tmpl_list.currentRow()
        if row < 0:
            return
        name = self.tmpl_list.item(row).text()
        if name in BUILTIN_TEMPLATES:
            QMessageBox.warning(self, "Cannot Delete", "Built-in templates cannot be deleted.")
            return
        path = cfg.templates_dir() / f"{name}.yaml"
        if path.exists():
            if QMessageBox.question(self, "Confirm", f"Delete '{name}'?") == QMessageBox.StandardButton.Yes:
                path.unlink()
                self._refresh_tmpl_list()
                self.templates_changed.emit()

    def _reset_template(self):
        row = self.tmpl_list.currentRow()
        if row < 0:
            return
        name = self.tmpl_list.item(row).text()
        if name not in BUILTIN_TEMPLATES:
            QMessageBox.information(self, "Info", "Only built-in templates can be reset.")
            return
        d = cfg.templates_dir()
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"{name}.yaml", "w", encoding="utf-8") as f:
            yaml.dump(BUILTIN_TEMPLATES[name], f, allow_unicode=True, default_flow_style=False)
        self._on_tmpl_select(row)


def _label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFixedWidth(90)
    lbl.setObjectName("card_label_small")
    return lbl
