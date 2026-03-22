"""History panel backed by SQLite."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal

from ytb_gui import config as cfg


class HistoryPanel(QWidget):
    rerun_requested = Signal(str)   # emits URL to re-run

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_db()
        self._build_ui()
        self.refresh()

    def _init_db(self):
        db_path = cfg.history_db()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                title TEXT,
                template TEXT,
                provider TEXT,
                output_path TEXT,
                created_at TEXT
            )
        """)
        self._conn.commit()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)

        open_btn = QPushButton("打开文件")
        open_btn.clicked.connect(self._open_selected)
        toolbar.addWidget(open_btn)

        rerun_btn = QPushButton("重新生成")
        rerun_btn.clicked.connect(self._rerun_selected)
        toolbar.addWidget(rerun_btn)

        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self._delete_selected)
        toolbar.addWidget(delete_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["时间", "标题", "Provider", "模板", "输出文件", "URL"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._open_selected)
        layout.addWidget(self.table)

    def add_entry(self, url: str, title: str, template: str, provider: str, output_path: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._conn.execute(
            "INSERT INTO history (url, title, template, provider, output_path, created_at) VALUES (?,?,?,?,?,?)",
            (url, title, template, provider, output_path, now),
        )
        self._conn.commit()
        self.refresh()

    def refresh(self):
        rows = self._conn.execute(
            "SELECT id, created_at, title, provider, template, output_path, url FROM history ORDER BY id DESC LIMIT 200"
        ).fetchall()

        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            rid, created_at, title, provider, template, output_path, url = row
            self.table.setItem(row_idx, 0, QTableWidgetItem(created_at))
            self.table.setItem(row_idx, 1, QTableWidgetItem(title or ""))
            self.table.setItem(row_idx, 2, QTableWidgetItem(provider or ""))
            self.table.setItem(row_idx, 3, QTableWidgetItem(template or ""))
            self.table.setItem(row_idx, 4, QTableWidgetItem(output_path or ""))
            self.table.setItem(row_idx, 5, QTableWidgetItem(url or ""))
            # Store row id as user data
            self.table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, rid)

    def _selected_row_data(self) -> tuple | None:
        rows = self.table.selectedItems()
        if not rows:
            return None
        row = self.table.currentRow()
        return (
            self.table.item(row, 0).data(Qt.ItemDataRole.UserRole),  # id
            self.table.item(row, 5).text(),  # url
            self.table.item(row, 4).text(),  # output_path
        )

    def _open_selected(self):
        data = self._selected_row_data()
        if not data:
            return
        _, _, output_path = data
        if not output_path:
            return
        p = Path(output_path)
        if not p.exists():
            return
        if sys.platform == "win32":
            os.startfile(str(p))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p)])

    def _rerun_selected(self):
        data = self._selected_row_data()
        if not data:
            return
        _, url, _ = data
        if url:
            self.rerun_requested.emit(url)

    def _delete_selected(self):
        data = self._selected_row_data()
        if not data:
            return
        rid, _, _ = data
        self._conn.execute("DELETE FROM history WHERE id=?", (rid,))
        self._conn.commit()
        self.refresh()
