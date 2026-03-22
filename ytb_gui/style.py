"""Dark theme QSS matching the HTML design."""

DARK_THEME = """
/* ── Base ─────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #060e20;
    color: #dee5ff;
    font-size: 13px;
}

QSplitter::handle { background: #2b4680; width: 1px; height: 1px; }

/* ── Sidebar ──────────────────────────────────────── */
#sidebar {
    background-color: #0a1530;
    border-right: 1px solid rgba(43,70,128,0.5);
}
#logo_box {
    background: transparent;
}
#logo_icon {
    background: #c6c6c7;
    border-radius: 4px;
    color: #3f4041;
    font-weight: 700;
    font-size: 15px;
}
#app_title {
    color: #e2e2e2;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 1px;
}
#app_subtitle {
    color: #5b74b1;
    font-size: 9px;
    letter-spacing: 2px;
}
#nav_btn {
    background: transparent;
    color: #909fb4;
    border: none;
    text-align: left;
    padding: 9px 14px;
    border-radius: 6px;
    font-size: 13px;
}
#nav_btn:hover {
    background: rgba(255,255,255,0.05);
    color: #dee5ff;
}
#nav_btn:checked {
    background: rgba(255,255,255,0.10);
    color: #dee5ff;
    font-weight: 500;
}
#status_dot_ok  { color: #34d399; font-size: 9px; }
#status_dot_err { color: #ee7d77; font-size: 9px; }
#footer_label   { color: #5b74b1; font-size: 9px; letter-spacing: 1px; }

/* ── Pages (main area) ────────────────────────────── */
#page_title {
    color: #dee5ff;
    font-size: 22px;
    font-weight: 700;
}
#page_subtitle { color: #909fb4; font-size: 13px; }

/* ── URL Input ────────────────────────────────────── */
#url_input {
    background: #06122d;
    border: none;
    border-bottom: 2px solid rgba(43,70,128,0.4);
    color: #dee5ff;
    font-size: 16px;
    padding: 18px 16px;
    border-radius: 0px;
    selection-background-color: #2b4680;
}
#url_input:focus { border-bottom: 2px solid #5b74b1; }

#summarize_btn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #c6c6c7, stop:1 #b0b0b1);
    color: #1a1a1a;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    padding: 0 28px;
    min-height: 44px;
}
#summarize_btn:hover   { background: #d8d8d9; }
#summarize_btn:pressed { background: #a0a0a1; }
#summarize_btn:disabled{ background: #1e2d50; color: #5b74b1; }

#stop_btn {
    background: transparent;
    color: #ee7d77;
    border: 1px solid rgba(238,125,119,0.3);
    border-radius: 6px;
    padding: 0 18px;
    min-height: 44px;
    font-size: 13px;
}
#stop_btn:hover   { background: rgba(238,125,119,0.1); }
#stop_btn:disabled{ color: #2b4680; border-color: #2b4680; }

/* ── Setting Cards ────────────────────────────────── */
#settings_card {
    background: #06122d;
    border: 1px solid rgba(43,70,128,0.25);
    border-radius: 10px;
    padding: 4px;
}
#card_label_small {
    color: #5b74b1;
    font-size: 9px;
    letter-spacing: 2px;
}
#card_value {
    color: #dee5ff;
    font-size: 13px;
    font-weight: 500;
}

/* ── Progress / Log ───────────────────────────────── */
#log_view {
    background: #031d4b;
    color: #909fb4;
    border: none;
    font-family: "Consolas", "Ubuntu Mono", monospace;
    font-size: 11px;
    padding: 8px;
}
QProgressBar {
    background: #031d4b;
    border: none;
    border-radius: 2px;
    max-height: 3px;
}
QProgressBar::chunk { background: #c6c6c7; border-radius: 2px; }

/* ── Preview ──────────────────────────────────────── */
#preview_toolbar QPushButton {
    background: #05183c;
    color: #909fb4;
    border: 1px solid #2b4680;
    border-radius: 4px;
    padding: 4px 12px;
    font-size: 11px;
}
#preview_toolbar QPushButton:hover { color: #dee5ff; }

QTextBrowser {
    background: #06122d;
    color: #dee5ff;
    border: none;
    font-size: 13px;
    padding: 8px;
    selection-background-color: #2b4680;
}

/* ── History Table ────────────────────────────────── */
QTableWidget {
    background: #06122d;
    alternate-background-color: #05183c;
    gridline-color: rgba(43,70,128,0.3);
    color: #dee5ff;
    border: none;
    selection-background-color: #0e2550;
}
QHeaderView::section {
    background: #05183c;
    color: #5b74b1;
    padding: 7px 10px;
    border: none;
    border-bottom: 1px solid rgba(43,70,128,0.5);
    font-size: 10px;
    letter-spacing: 1px;
}
QTableWidget::item { padding: 6px 10px; }
QTableWidget::item:selected { background: #0e2550; color: #dee5ff; }

/* ── Template Editor ──────────────────────────────── */
QListWidget {
    background: #05183c;
    border: 1px solid rgba(43,70,128,0.3);
    border-radius: 6px;
    color: #dee5ff;
    padding: 4px;
}
QListWidget::item { padding: 7px 10px; border-radius: 4px; }
QListWidget::item:selected { background: #0e2550; }
QListWidget::item:hover    { background: rgba(255,255,255,0.04); }

QPlainTextEdit {
    background: #031d4b;
    color: #dee5ff;
    border: 1px solid rgba(43,70,128,0.3);
    border-radius: 6px;
    font-family: "Consolas", "Ubuntu Mono", monospace;
    font-size: 12px;
    selection-background-color: #2b4680;
}

/* ── General Inputs ───────────────────────────────── */
QLineEdit, QComboBox {
    background: #05183c;
    color: #dee5ff;
    border: 1px solid rgba(43,70,128,0.5);
    border-radius: 5px;
    padding: 6px 10px;
    selection-background-color: #2b4680;
}
QLineEdit:focus, QComboBox:focus { border-color: #5b74b1; }

QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow { width: 0; height: 0; }
QComboBox QAbstractItemView {
    background: #05183c;
    color: #dee5ff;
    border: 1px solid #2b4680;
    selection-background-color: #0e2550;
    outline: none;
}

/* ── General Buttons ──────────────────────────────── */
QPushButton {
    background: #05183c;
    color: #909fb4;
    border: 1px solid rgba(43,70,128,0.5);
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 12px;
}
QPushButton:hover   { background: #06122d; color: #dee5ff; border-color: #5b74b1; }
QPushButton:pressed { background: #031d4b; }
QPushButton:disabled{ color: #2b4680; border-color: rgba(43,70,128,0.3); }

/* ── Status Bar ───────────────────────────────────── */
QStatusBar {
    background: #060e20;
    color: #5b74b1;
    border-top: 1px solid rgba(43,70,128,0.4);
    font-size: 10px;
    letter-spacing: 1px;
}
QStatusBar::item { border: none; }

/* ── ScrollBar ────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2b4680;
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
}
QScrollBar::handle:horizontal {
    background: #2b4680;
    border-radius: 3px;
    min-width: 24px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Divider ──────────────────────────────────────── */
#divider {
    background: rgba(43,70,128,0.5);
    max-height: 1px;
    min-height: 1px;
}

/* ── Message Box ──────────────────────────────────── */
QMessageBox {
    background: #05183c;
}
QMessageBox QPushButton { min-width: 80px; }

/* ── Input Dialog ─────────────────────────────────── */
QInputDialog {
    background: #05183c;
}
"""
