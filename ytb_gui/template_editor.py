"""Template editor panel: list + YAML editor."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QPushButton,
    QPlainTextEdit, QLabel, QInputDialog, QMessageBox, QSplitter,
)
from PySide6.QtCore import Qt, Signal

import yaml

from ytb_summarizer.templates import BUILTIN_TEMPLATES, list_templates, get_template
from ytb_gui import config as cfg


class TemplateEditor(QWidget):
    templates_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        layout = QHBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left: list + buttons ──
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("模板列表"))

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_select)
        left_layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        new_btn = QPushButton("新建")
        new_btn.clicked.connect(self._new_template)
        btn_row.addWidget(new_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save_template)
        btn_row.addWidget(save_btn)

        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self._delete_template)
        btn_row.addWidget(delete_btn)

        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self._reset_template)
        btn_row.addWidget(reset_btn)

        left_layout.addLayout(btn_row)
        splitter.addWidget(left)

        # ── Right: YAML editor ──
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("YAML 编辑"))

        self.editor = QPlainTextEdit()
        self.editor.setFont(_monospace_font())
        right_layout.addWidget(self.editor)
        splitter.addWidget(right)

        splitter.setSizes([200, 600])
        layout.addWidget(splitter)

    def _refresh_list(self):
        self.list_widget.clear()
        names = list_templates(custom_dir=cfg.templates_dir())
        for name in names:
            self.list_widget.addItem(name)

    def _on_select(self, row: int):
        if row < 0:
            return
        name = self.list_widget.item(row).text()
        try:
            tmpl = get_template(name, custom_dir=cfg.templates_dir())
            self.editor.setPlainText(yaml.dump(tmpl, allow_unicode=True, default_flow_style=False))
        except Exception as e:
            self.editor.setPlainText(f"# Error loading template: {e}")

    def _new_template(self):
        name, ok = QInputDialog.getText(self, "新建模板", "模板名称:")
        if not ok or not name.strip():
            return
        name = name.strip()
        custom_dir = cfg.templates_dir()
        custom_dir.mkdir(parents=True, exist_ok=True)
        path = custom_dir / f"{name}.yaml"
        template = {
            "name": name,
            "description": "自定义模板",
            "prompt": "请总结以下视频内容：\n\n视频标题：{title}\n\n字幕：{transcript}",
        }
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(template, f, allow_unicode=True, default_flow_style=False)
        self._refresh_list()
        self.templates_changed.emit()
        # Select the new item
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() == name:
                self.list_widget.setCurrentRow(i)
                break

    def _save_template(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        name = self.list_widget.item(row).text()
        content = self.editor.toPlainText()
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            QMessageBox.critical(self, "YAML 错误", str(e))
            return

        custom_dir = cfg.templates_dir()
        custom_dir.mkdir(parents=True, exist_ok=True)
        path = custom_dir / f"{name}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        self.templates_changed.emit()
        QMessageBox.information(self, "保存成功", f"模板 '{name}' 已保存。")

    def _delete_template(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        name = self.list_widget.item(row).text()
        if name in BUILTIN_TEMPLATES:
            QMessageBox.warning(self, "无法删除", "内置模板不能删除。")
            return
        custom_dir = cfg.templates_dir()
        path = custom_dir / f"{name}.yaml"
        if path.exists():
            reply = QMessageBox.question(self, "确认删除", f"确定删除模板 '{name}'？")
            if reply == QMessageBox.StandardButton.Yes:
                path.unlink()
                self._refresh_list()
                self.templates_changed.emit()

    def _reset_template(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        name = self.list_widget.item(row).text()
        if name not in BUILTIN_TEMPLATES:
            QMessageBox.information(self, "提示", "只有内置模板支持重置。")
            return
        custom_dir = cfg.templates_dir()
        path = custom_dir / f"{name}.yaml"
        import yaml as _yaml
        tmpl = BUILTIN_TEMPLATES[name]
        custom_dir.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            _yaml.dump(tmpl, f, allow_unicode=True, default_flow_style=False)
        self._on_select(row)
        QMessageBox.information(self, "重置成功", f"模板 '{name}' 已重置为默认值。")


def _monospace_font():
    from PySide6.QtGui import QFont
    font = QFont("Consolas", 10)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font
